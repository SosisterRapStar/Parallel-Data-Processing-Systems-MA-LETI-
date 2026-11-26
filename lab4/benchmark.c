#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

static void measure(int rank, int size, int per_column)
{
    const int sender_rank_in_column = 0;
    const int rows = size / 3;
    const int numbers_per_process = per_column / rows;
    int dims[] = {rows, 3}, periods[] = {0, 0}, keep[] = {1, 0};
    int *column_numbers = NULL, *received_numbers = malloc((size_t)numbers_per_process * sizeof(*received_numbers));
    if (!received_numbers)
        MPI_Abort(MPI_COMM_WORLD, 1);
    if (rank < 3) {
        column_numbers = malloc((size_t)per_column * sizeof(*column_numbers));
        if (!column_numbers)
            MPI_Abort(MPI_COMM_WORLD, 1);
        for (int i = 0; i < per_column; i++)
            column_numbers[i] = 10 * (rank + 1) + i;
    }
    for (int rep = -3; rep < 31; rep++) {
        MPI_Comm grid, column_comm;
        MPI_Barrier(MPI_COMM_WORLD);
        double start = MPI_Wtime();
        MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 0, &grid);
        MPI_Cart_sub(grid, keep, &column_comm);
        MPI_Scatter(
            column_numbers,        // sendbuf: массив чисел у отправителя
            numbers_per_process,   // sendcount: сколько чисел выделить каждому процессу
            MPI_INT,               // sendtype: тип элемента исходного массива
            received_numbers,      // recvbuf: куда этот процесс запишет свою часть
            numbers_per_process,   // recvcount: сколько чисел примет этот процесс
            MPI_INT,               // recvtype: тип принимаемого элемента
            sender_rank_in_column, // root: номер отправителя внутри столбца
            column_comm            // comm: группа процессов этого столбца
        );
        double elapsed = MPI_Wtime() - start;
        double maximum;
        MPI_Reduce(&elapsed, &maximum, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
        for (int i = 0; i < numbers_per_process; i++) {
            if (received_numbers[i] != 10 * (rank % 3 + 1) + rank / 3 * numbers_per_process + i)
                MPI_Abort(MPI_COMM_WORLD, 2);
        }
        MPI_Comm_free(&column_comm);
        MPI_Comm_free(&grid);
        if (rep >= 0 && rank == 0)
            printf("%d,%d,%d,%d,%.9f\n", size, per_column, numbers_per_process, rep, maximum);
    }
    free(received_numbers);
    free(column_numbers);
}

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);
    int size, rank;
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    if (size < 6 || size % 3 != 0 || 6000 % (size / 3) != 0) {
        if (rank == 0)
            fputs("Unsupported process grid for this measurement series\n", stderr);
        MPI_Finalize();
        return 1;
    }
    measure(rank, size, size / 3);
    measure(rank, size, 6000);
    measure(rank, size, 60000);
    MPI_Finalize();
    return 0;
}
