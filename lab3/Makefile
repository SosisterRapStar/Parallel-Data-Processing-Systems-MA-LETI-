CC = mpicc
CFLAGS = -O2 -std=c11 -Wall -Wextra -Wpedantic

all: lab3 benchmark

lab3: main.c
	$(CC) $(CFLAGS) $< -o $@

benchmark: benchmark.c
	$(CC) $(CFLAGS) $< -o $@

clean:
	rm -f lab3 benchmark

.PHONY: all clean
