#include <mpi.h>
#include <stdbool.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argumentCount, char **arguments) {
    MPI_Init(&argumentCount, &arguments);

    int rank;
    int processCount;
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &processCount);

    if (argumentCount != 2) {
        if (rank == 0) {
            fprintf(stderr, "Usage: lab1 ordered|unordered\n");
        }
        MPI_Abort(MPI_COMM_WORLD, 1);
        return 1;
    }

    char *mode = arguments[1];
    bool ordered = strcmp(mode, "ordered") == 0;
    bool unordered = strcmp(mode, "unordered") == 0;

    if (ordered == false && unordered == false) {
        if (rank == 0) {
            fprintf(stderr, "Unknown mode: %s\n", mode);
        }
        MPI_Abort(MPI_COMM_WORLD, 1);
        return 1;
    }

    int *receivedRanks = malloc(processCount * sizeof(int));

    if (receivedRanks == NULL) {
        MPI_Abort(MPI_COMM_WORLD, 2);
        return 2;
    }

    receivedRanks[0] = 0;

    if (rank == 0) {
        printf("ranks: 0");
        fflush(stdout);
    }

    MPI_Barrier(MPI_COMM_WORLD);
    double startTime = MPI_Wtime();

    if (rank != 0) {
        // Каждый рабочий процесс отправляет свой ранг процессу 0.
        MPI_Send(&rank, 1, MPI_INT, 0, 0, MPI_COMM_WORLD);
    }

    if (rank == 0) {
        for (int messageIndex = 1; messageIndex < processCount; messageIndex++) {
            int senderRank = MPI_ANY_SOURCE;
            if (ordered == true) {
                senderRank = messageIndex;
            }

            int receivedRank;
            MPI_Status messageStatus;
            MPI_Recv(&receivedRank, 1, MPI_INT, senderRank,
                     0, MPI_COMM_WORLD, &messageStatus);

            int actualSenderRank = messageStatus.MPI_SOURCE;
            if (receivedRank != actualSenderRank) {
                MPI_Abort(MPI_COMM_WORLD, 4);
                return 4;
            }

            receivedRanks[messageIndex] = receivedRank;
        }
    }

    double elapsedTime = MPI_Wtime() - startTime;
    double maximumTime;
    MPI_Reduce(&elapsedTime, &maximumTime, 1, MPI_DOUBLE,
               MPI_MAX, 0, MPI_COMM_WORLD);

    if (rank == 0) {
        for (int messageIndex = 1; messageIndex < processCount; messageIndex++) {
            printf(" %d", receivedRanks[messageIndex]);
        }
        printf("\nmode=%s processes=%d ints=1 seconds=%.9g\n",
               mode, processCount, maximumTime);
    }

    free(receivedRanks);
    MPI_Finalize();
    return 0;
}
