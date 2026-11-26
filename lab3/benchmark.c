#include <errno.h>
#include <limits.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum { Rows = 32, Period = 1000, Warmups = 2, Samples = 7 };

static int parse_length(const char *text)
{
    char *end;
    errno = 0;
    long length = strtol(text, &end, 10);
    if (errno != 0 || end == text || *end != '\0' ||
        length < 1 || length > INT_MAX) {
        return 0;
    }
    return (int)length;
}

static int *allocate_array(size_t length)
{
    int *array = calloc(length ? length : 1, sizeof(*array));
    if (array == NULL) {
        fprintf(stderr, "Cannot allocate array\n");
        MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    }
    return array;
}

static void fill_rows(int *data, int length, int first_row, int rows)
{
    for (int row = 0; row < rows; row++) {
        int *values = data + (size_t)row * length;
        for (int col = 0; col < length; col++) {
            values[col] = (first_row + row + col % Period) % Period;
        }
    }
}

static void sum_rows(const int *data, int *partial, int length, int rows)
{
    memset(partial, 0, (size_t)length * sizeof(*partial));
    for (int row = 0; row < rows; row++) {
        const int *values = data + (size_t)row * length;
        for (int col = 0; col < length; col++) {
            partial[col] += values[col];
        }
    }
}

static int verify(const int *result, int length, int rows)
{
    int expected[Period] = {0};
    for (int row = 0; row < rows; row++) {
        for (int col = 0; col < Period; col++) {
            expected[col] += (row + col) % Period;
        }
    }
    for (int col = 0; col < length; col++) {
        if (result[col] != expected[col % Period]) {
            return 0;
        }
    }
    return 1;
}

int main(int argc, char **argv)
{
    MPI_Init(&argc, &argv);

    int rank, processes;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &processes);

    int variant = argc == 2 && strcmp(argv[1], "variant") == 0;
    int length = argc == 2 ? parse_length(argv[1]) : 0;
    if (variant && processes <= INT_MAX / (Period - 1)) {
        length = processes + 5;
    }
    if (length == 0) {
        if (rank == 0) {
            fprintf(stderr, "Usage: benchmark variant|positive-length\n");
        }
        MPI_Finalize();
        return EXIT_FAILURE;
    }

    int total_rows = variant ? processes : Rows;
    int remainder = total_rows % processes;
    int rows = total_rows / processes + (rank < remainder);
    int first_row = rank * (total_rows / processes) +
                    (rank < remainder ? rank : remainder);
    int *data = allocate_array((size_t)rows * length);
    int *partial = variant ? data : allocate_array(length);
    int *result = rank == 0 ? allocate_array(length) : NULL;
    fill_rows(data, length, first_row, rows);

    double elapsed[Samples];
    for (int iteration = -Warmups; iteration < Samples; iteration++) {
        MPI_Barrier(MPI_COMM_WORLD);
        double start = MPI_Wtime();
        if (!variant) {
            sum_rows(data, partial, length, rows);
        }
        MPI_Reduce(partial, result, length, MPI_INT,
                   MPI_SUM, 0, MPI_COMM_WORLD);
        double duration = MPI_Wtime() - start;
        if (iteration >= 0) {
            elapsed[iteration] = duration;
        }
    }

    double maximum[Samples];
    MPI_Reduce(elapsed, maximum, Samples, MPI_DOUBLE,
               MPI_MAX, 0, MPI_COMM_WORLD);

    int status = EXIT_SUCCESS;
    if (rank == 0) {
        int correct = verify(result, length, total_rows);
        for (int sample = 0; sample < Samples; sample++) {
            printf("%s,%d,%d,%d,%d,%.12g,%d\n",
                   variant ? "variant" : "fixed", length, processes,
                   total_rows, sample + 1, maximum[sample], correct);
        }
        status = correct ? EXIT_SUCCESS : EXIT_FAILURE;
    }

    if (!variant) {
        free(partial);
    }
    free(result);
    free(data);
    MPI_Finalize();
    return status;
}
