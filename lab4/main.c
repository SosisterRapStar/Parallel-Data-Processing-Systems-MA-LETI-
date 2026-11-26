#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int size, rank;
    MPI_Comm_size(MPI_COMM_WORLD, &size);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    if (size < 6 || size % 3 != 0) {
        if (rank == 0)
            fprintf(stderr, "Число процессов должно быть кратно 3 и не меньше 6.\n");
        MPI_Finalize();
        return 1;
    }

    int rows = size / 3;
    int dims[] = {rows, 3};
    int periods[] = {0, 0};
    MPI_Comm grid, column_comm;
    MPI_Cart_create(MPI_COMM_WORLD, 2, dims, periods, 0, &grid);

    int keep[] = {1, 0};
    MPI_Cart_sub(grid, keep, &column_comm);

    const int sender_rank_in_column = 0;
    int rank_in_column;
    MPI_Comm_rank(column_comm, &rank_in_column);
    int *column_numbers = NULL;
    if (rank_in_column == sender_rank_in_column) {
        column_numbers = malloc((size_t)rows * sizeof(*column_numbers));
        if (column_numbers == NULL)
            MPI_Abort(MPI_COMM_WORLD, 1);
        for (int i = 0; i < rows; i++)
            column_numbers[i] = 10 * (rank + 1) + i;
    }

    int received_number;
    MPI_Scatter(
        column_numbers,        // sendbuf: массив чисел у отправителя
        1,                     // sendcount: сколько чисел выделить каждому процессу
        MPI_INT,               // sendtype: тип элемента исходного массива
        &received_number,      // recvbuf: куда этот процесс запишет свою часть
        1,                     // recvcount: сколько чисел примет этот процесс
        MPI_INT,               // recvtype: тип принимаемого элемента
        sender_rank_in_column, // root: номер отправителя внутри столбца
        column_comm            // comm: группа процессов этого столбца
    );
    printf("Процесс %d получил %d\n", rank, received_number);

    free(column_numbers);
    MPI_Comm_free(&column_comm);
    MPI_Comm_free(&grid);
    MPI_Finalize();
    return 0;
}
