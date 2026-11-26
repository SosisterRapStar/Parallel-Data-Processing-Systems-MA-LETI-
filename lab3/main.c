#include <limits.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>

static int *allocate_array(int length)
{
    int *array = malloc((size_t)length * sizeof(*array));
    if (array == NULL) {
        fprintf(stderr, "Cannot allocate array\n");
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
    return array;
}

static void print_sums(const int *sums, int length)
{
    printf("Sums:");
    for (int index = 0; index < length; index++) {
        printf(" %d", sums[index]);
    }
    putchar('\n');
}

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank, processes;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &processes);

    // The generated values are in [0, 999].
    if (processes > INT_MAX / 999) {
        MPI_Finalize();
        return EXIT_FAILURE;
    }

    int length = processes + 5;
    int *values = allocate_array(length);
    for (int index = 0; index < length; index++) {
        values[index] = (rank + index) % 1000;
    }

    int *sums = rank == 0 ? allocate_array(length) : NULL;
    MPI_Reduce(values, sums, length, MPI_INT,
               MPI_SUM, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        print_sums(sums, length);
    }

    free(sums);
    free(values);
    MPI_Finalize();
    return EXIT_SUCCESS;
}
