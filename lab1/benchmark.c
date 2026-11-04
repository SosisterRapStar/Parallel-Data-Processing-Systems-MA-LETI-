#include <mpi.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
int main(int argc, char **argv) {
    MPI_Init(&argc, &argv);
    int rank, p;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &p);
    int ordered = argc > 1 && strcmp(argv[1], "ordered") == 0;
    long n = argc > 2 ? strtol(argv[2], NULL, 10) : 1;
    if (argc < 2 || (strcmp(argv[1], "ordered") && strcmp(argv[1], "unordered")) || n < 1 || n > INT_MAX) {
        if (!rank) fprintf(stderr, "Usage: lab1 ordered|unordered [message_ints]\n");
        MPI_Abort(MPI_COMM_WORLD, 1);
    }
    int *buf = malloc((size_t)n * sizeof(int));
    int *seen = calloc((size_t)p, sizeof(int));
    int *order = malloc((size_t)p * sizeof(int));
    if (!buf || !seen || !order) MPI_Abort(MPI_COMM_WORLD, 2);
    for (long i = 0; i < n; ++i) buf[i] = rank;
    order[0] = 0; seen[0] = 1;
    /* Generation and printing are outside the measured interval. */
    if (!rank) { printf("ranks: 0"); fflush(stdout); }
    MPI_Barrier(MPI_COMM_WORLD);
    double start = MPI_Wtime();
    if (rank) MPI_Send(buf, (int)n, MPI_INT, 0, 0, MPI_COMM_WORLD);
    else for (int i = 1; i < p; ++i) {
        MPI_Status status;
        MPI_Recv(buf, (int)n, MPI_INT, ordered ? i : MPI_ANY_SOURCE,
                 0, MPI_COMM_WORLD, &status);
        int source = status.MPI_SOURCE;
        if (seen[source]++) MPI_Abort(MPI_COMM_WORLD, 3);
        for (long j = 0; j < n; ++j)
            if (buf[j] != source) MPI_Abort(MPI_COMM_WORLD, 4);
        order[i] = source;
    }
    double elapsed = MPI_Wtime() - start, total;
    MPI_Reduce(&elapsed, &total, 1, MPI_DOUBLE, MPI_MAX, 0, MPI_COMM_WORLD);
    if (!rank) {
        for (int i = 1; i < p; ++i) printf(" %d", order[i]);
        printf("\nmode=%s processes=%d ints=%ld seconds=%.9g\n",
               ordered ? "ordered" : "unordered", p, n, total);
    }
    free(buf); free(seen); free(order);
    MPI_Finalize();
    return 0;
}
