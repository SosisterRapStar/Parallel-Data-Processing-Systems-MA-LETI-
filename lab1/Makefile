CC = mpicc
CFLAGS = -O2 -std=c11 -Wall -Wextra -Wpedantic
lab1: main.c
	$(CC) $(CFLAGS) $< -o $@
clean:
	rm -f lab1
.PHONY: clean

benchmark: benchmark.c
	$(CC) $(CFLAGS) $< -o $@
