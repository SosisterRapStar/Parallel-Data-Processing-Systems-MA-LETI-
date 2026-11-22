"""Сеть Петри коллективного суммирования в ПР № 3."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

OUT = Path(__file__).resolve().parent / "results"
RANKS = ((1, 1.35), (0, 5.30), (2, 9.25))
INK = "#172c40"
BLUE = "#275c90"


def draw(filename, height, positions, transitions, edges, marking, labels, notes, left_labels):
    # Как в ПР № 1 и № 2: координаты, круги, прямоугольники и дуги.
    width = 13.2
    fig, ax = plt.subplots(figsize=(width * 0.67, height * 0.67))
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    ax.set(xlim=(0, width), ylim=(0, height), aspect="equal")
    ax.axis("off")

    nodes = {}
    for name, (x, y) in positions.items():
        circle = Circle((x, y), .23, facecolor="white", edgecolor=INK, lw=1.5, zorder=3)
        ax.add_patch(circle)
        nodes[name] = circle
        if marking.get(name) == 1:
            ax.plot(x, y, "o", color=INK, markersize=4.5, zorder=4)
        if marking.get(name, 0) > 1:
            ax.text(x, y, str(marking[name]), ha="center", va="center", zorder=4)
        if name in left_labels:
            ax.text(x - .33, y, labels[name], ha="right", va="center", fontsize=10, color=INK)
        else:
            ax.text(x + .33, y, labels[name], va="center", fontsize=10, color=INK)

    for name, (x, y, label) in transitions.items():
        bar = Rectangle((x - .28, y - .1), .56, .2, color=BLUE, zorder=3)
        ax.add_patch(bar)
        nodes[name] = bar
        ax.text(x + .38, y, label, va="center", fontsize=9.5, color=INK,
                bbox=dict(facecolor="white", edgecolor="none", pad=.3), zorder=5)

    coords = positions | {name: (x, y) for name, (x, y, _) in transitions.items()}
    for source, target in edges:
        ax.annotate("", xy=coords[target], xytext=coords[source],
                    arrowprops=dict(arrowstyle="->", color="#526273", lw=1.4,
                                    patchA=nodes[source], patchB=nodes[target],
                                    shrinkA=1, shrinkB=1), zorder=2)

    for x, y, label in notes:
        ax.text(x, y, label, ha="center", va="center", fontsize=10, color=INK)

    fig.savefig(OUT / filename, dpi=220)
    plt.close(fig)


def reduction():
    positions = {"sum_ready": (6.2, 3.34)}
    transitions = {"sum": (6.2, 4.65, "MPI_Reduce с MPI_SUM")}
    edges = [("sum", "sum_ready")]
    marking = {}
    labels = {"sum_ready": "Суммы готовы"}
    notes = []
    left_labels = set()

    for rank, x in RANKS:
        ready, waiting, contribution, done, buffer_available = (
            f"{state}_{rank}" for state in
            ("ready", "waiting", "contribution", "done", "buffer_available")
        )
        enter, release, ret = (f"{step}_{rank}" for step in ("enter", "release", "return"))
        positions.update({
            ready: (x, 8.27), waiting: (x, 6.28),
            contribution: (x + 1.55, 5.78), done: (x, 1.21),
        })
        labels.update({
            ready: "Входные данные готовы",
            waiting: "Корень\nждёт сумму" if rank == 0 else "Внутри\nвызова",
            contribution: f"Вклад ранга {rank}",
            done: "Суммы у процесса 0" if rank == 0 else "Вызов завершён",
        })
        left_labels.add(waiting)
        transitions[enter] = (x, 7.32, "MPI_Reduce — вход")
        transitions[ret] = (x, 2.27, "MPI_Reduce — возврат")
        marking[ready] = 1
        title = f"Ранг {rank}" + (" (корень)" if rank == 0 else "")
        notes.append((x + .6, 8.98, title))
        edges.extend([
            (ready, enter), (enter, waiting), (enter, contribution),
            (contribution, "sum"), (ret, done),
        ])
        if rank == 0:
            edges.extend([(waiting, ret), ("sum_ready", ret)])
        else:
            positions[buffer_available] = (x, 3.34)
            labels[buffer_available] = "Буфер можно менять"
            transitions[release] = (x, 4.0, "MPI_Reduce — конец чтения")
            edges.extend([
                (waiting, release), (release, buffer_available), (buffer_available, ret),
            ])

    draw("petri-reduce.png", 9.4, positions, transitions, edges, marking, labels, notes, left_labels)


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    reduction()
