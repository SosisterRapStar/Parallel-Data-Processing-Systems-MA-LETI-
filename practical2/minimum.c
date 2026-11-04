#include <errno.h>
#include <limits.h>
#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

enum {
    Root = 0,
    DefaultSize = 1000000,
    SampleCount = 7,
    DataTag = 1,
    MinimumTag = 2,
    ReadyTag = 9,
    StartTag = 10,
};

static int parse_size(int argc, char **argv) {
    if (argc == 1) {
        return DefaultSize;
    }
    if (argc != 2) {
        return 0;
    }

    char *end;
    errno = 0;
    long size = strtol(argv[1], &end, 10);
    if (errno != 0 || end == argv[1] || *end != '\0') {
        return 0;
    }
    if (size < 1 || size > INT_MAX) {
        return 0;
    }
    return (int)size;
}

static int *allocate_array(int count) {
    // Even an empty block needs a valid buffer for an MPI call.
    size_t capacity = count > 0 ? (size_t)count : 1;
    int *values = malloc(capacity * sizeof(*values));
    if (values != NULL) {
        return values;
    }

    fprintf(stderr, "Cannot allocate array\n");
    MPI_Abort(MPI_COMM_WORLD, EXIT_FAILURE);
    exit(EXIT_FAILURE);
}

static int block_size(int size, int processes, int rank) {
    return size / processes + (rank < size % processes);
}

static int minimum(int left, int right) {
    return left < right ? left : right;
}

static int array_minimum(const int *values, int count) {
    int result = INT_MAX;
    for (int i = 0; i < count; i++) {
        result = minimum(result, values[i]);
    }
    return result;
}

static int *generate_array(int size) {
    int *values = allocate_array(size);
    srand(42);
    for (int i = 0; i < size; i++) {
        values[i] = rand();
    }
    return values;
}

static void synchronize(int rank, int processes) {
    int token = 1;
    if (rank != Root) {
        MPI_Send(&token, 1, MPI_INT, Root, ReadyTag, MPI_COMM_WORLD);
        MPI_Recv(&token, 1, MPI_INT, Root, StartTag,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        return;
    }

    for (int worker = 1; worker < processes; worker++) {
        MPI_Recv(&token, 1, MPI_INT, worker, ReadyTag,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
    }
    for (int worker = 1; worker < processes; worker++) {
        MPI_Send(&token, 1, MPI_INT, worker, StartTag, MPI_COMM_WORLD);
    }
}

static void distribute(const int *values, int size, int *local,
                       int rank, int processes) {
    int count = block_size(size, processes, rank);
    if (rank != Root) {
        MPI_Recv(local, count, MPI_INT, Root, DataTag,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        return;
    }

    int offset = count;
    for (int worker = 1; worker < processes; worker++) {
        int worker_count = block_size(size, processes, worker);
        MPI_Send(values + offset, worker_count, MPI_INT,
                 worker, DataTag, MPI_COMM_WORLD);
        offset += worker_count;
    }
    memcpy(local, values, (size_t)count * sizeof(*local));
}

static int collect_minimum(int local_minimum, int rank, int processes) {
    if (rank != Root) {
        MPI_Send(&local_minimum, 1, MPI_INT, Root, MinimumTag, MPI_COMM_WORLD);
        return local_minimum;
    }

    int result = local_minimum;
    for (int worker = 1; worker < processes; worker++) {
        int worker_minimum;
        MPI_Recv(&worker_minimum, 1, MPI_INT, worker, MinimumTag,
                 MPI_COMM_WORLD, MPI_STATUS_IGNORE);
        result = minimum(result, worker_minimum);
    }
    return result;
}

static int compare_times(const void *left, const void *right) {
    double a = *(const double *)left;
    double b = *(const double *)right;
    return (a > b) - (a < b);
}

static void print_result(int size, int processes, double *times,
                         int result, int expected) {
    qsort(times, SampleCount, sizeof(*times), compare_times);
    double median = times[SampleCount / 2];
    // CSV: n,p,seconds,minimum,correct.
    printf("%d,%d,%.9f,%d,%d\n",
           size, processes, median, result, result == expected);
}

int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank;
    int processes;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &processes);

    int size = parse_size(argc, argv);
    if (size == 0) {
        if (rank == Root) {
            fprintf(stderr, "Usage: %s [positive array size]\n", argv[0]);
        }
        MPI_Finalize();
        return EXIT_FAILURE;
    }

    int count = block_size(size, processes, rank);
    int *local = allocate_array(count);
    int *values = NULL;
    int expected = INT_MAX;
    if (rank == Root) {
        values = generate_array(size);
        expected = array_minimum(values, size);
    }

    double times[SampleCount];
    int result = INT_MAX;
    // Iteration 0 warms up MPI and memory; the next seven are measured.
    for (int iteration = 0; iteration <= SampleCount; iteration++) {
        synchronize(rank, processes);
        double start = MPI_Wtime();
        distribute(values, size, local, rank, processes);
        int local_minimum = array_minimum(local, count);
        result = collect_minimum(local_minimum, rank, processes);
        double elapsed = MPI_Wtime() - start;

        if (rank != Root || iteration == 0) {
            continue;
        }
        times[iteration - 1] = elapsed;
    }

    if (rank == Root) {
        print_result(size, processes, times, result, expected);
    }
    free(values);
    free(local);
    MPI_Finalize();
    return EXIT_SUCCESS;
}
