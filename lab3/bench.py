"""Run MPI benchmarks and plot strong scaling of the fixed workload."""
import argparse
import csv
from pathlib import Path
from statistics import median
from subprocess import check_output

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

DIRECTORY = Path(__file__).resolve().parent
RESULTS = DIRECTORY / "results"
FIELDS = ("mode", "length", "processes", "rows", "sample", "seconds", "correct")


def measure(raw_path, process_counts, lengths, allow_oversubscription):
    summaries = []
    with raw_path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=FIELDS)
        writer.writeheader()
        for workload in ("variant", *lengths):
            baseline = None
            for processes in process_counts:
                command = ["mpirun", "--bind-to", "none"]
                if allow_oversubscription:
                    command.append("--oversubscribe")
                output = check_output([
                    *command,
                    "-np", str(processes), str(DIRECTORY / "benchmark"), str(workload),
                ], text=True, timeout=90)
                samples = list(csv.DictReader(output.splitlines(), fieldnames=FIELDS))
                if len(samples) != 7 or any(row["correct"] != "1" for row in samples):
                    raise RuntimeError(f"Unexpected result: {workload=}, {processes=}")
                writer.writerows(samples)
                file.flush()
                elapsed = median(float(row["seconds"]) for row in samples)
                if processes == 1:
                    baseline = elapsed
                summary = dict(samples[0])
                summary.pop("sample")
                summary["seconds"] = elapsed
                summary["speedup"] = baseline / elapsed if workload != "variant" else ""
                summaries.append(summary)
                print(f"{workload!s:>8} | p={processes:2} | {elapsed*1000:.6f} ms", flush=True)
    return summaries


def plot(summaries, metric, path, label, process_counts, lengths):
    figure, axis = plt.subplots(figsize=(7.2, 4))
    for length in lengths:
        series = [row for row in summaries if row["mode"] == "fixed"
                  and int(row["length"]) == length]
        units = 1000 if metric == "seconds" else 1
        axis.plot(process_counts, [row[metric] * units for row in series],
                  marker="o", label=f"n = {length:,}".replace(",", " "))
    axis.set_xscale("log", base=2)
    axis.set_xticks(process_counts, [str(p) for p in process_counts])
    if metric == "seconds":
        axis.set_yscale("log")
    else:
        axis.axhline(1, color="0.55", linestyle="--", linewidth=1)
    axis.set(xlabel="Число процессов p", ylabel=label)
    axis.grid(True, alpha=0.3)
    axis.legend()
    figure.tight_layout()
    figure.savefig(path, dpi=220)
    plt.close(figure)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--full", action="store_true",
                        help="run the report workload (up to 32 ranks and 4M elements per row)")
    args = parser.parse_args()
    process_counts = (1, 2, 4, 8, 16, 32) if args.full else (1, 2, 4)
    lengths = (10_000, 1_000_000, 4_000_000) if args.full else (10_000, 100_000)
    output = RESULTS if args.full else RESULTS / "quick"
    output.mkdir(parents=True, exist_ok=True)
    summaries = measure(output / "samples.csv", process_counts, lengths, args.full)
    with (output / "summary.csv").open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=list(summaries[0]))
        writer.writeheader()
        writer.writerows(summaries)
    plot(summaries, "seconds", output / "time.png", "Время, мс", process_counts, lengths)
    plot(summaries, "speedup", output / "speedup.png", "Ускорение", process_counts, lengths)


if __name__ == "__main__":
    main()
