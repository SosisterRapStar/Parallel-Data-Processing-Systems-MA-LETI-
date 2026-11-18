"""Draw the colored Petri net of the timed part of the program."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Ellipse, FancyArrowPatch, Rectangle

OUT = Path(__file__).resolve().parent / "results"
BLUE = "#244d76"
INK = "#17283b"


def canvas(ymax, size):
    figure, axes = plt.subplots(figsize=size)
    axes.set(xlim=(0, 12), ylim=(0, ymax))
    axes.axis("off")
    return figure, axes


def place(axes, x, y, label, width=3.3, initial=False):
    axes.add_patch(Ellipse((x, y), width, 0.76, fc="#edf4fb",
                           ec=BLUE, linewidth=1.5, zorder=3))
    if initial:
        label += "  ●"
    axes.text(x, y, label, ha="center", va="center", color=INK, fontsize=11, zorder=4)


def transition(axes, x, y, label, width=3.2):
    axes.add_patch(Rectangle((x-width/2, y-0.32), width, 0.64,
                             fc=BLUE, ec=BLUE, zorder=3))
    axes.text(x, y, label, ha="center", va="center", color="white", fontsize=11, zorder=4)


def arrow(axes, start, end, label="", bend=0, label_position=None):
    axes.add_patch(FancyArrowPatch(start, end, arrowstyle="-|>",
                                  mutation_scale=12, color=INK, linewidth=1.25,
                                  connectionstyle=f"arc3,rad={bend}", zorder=2))
    if label:
        axes.text(*label_position, label, ha="center", va="center", fontsize=10,
                  color=INK, bbox=dict(facecolor="white", edgecolor="none", pad=1))


def save(figure, filename):
    figure.subplots_adjust(left=0.015, right=0.985, top=0.99, bottom=0.01)
    figure.savefig(OUT / filename, dpi=240)
    plt.close(figure)


def draw_cycle():
    figure, axes = canvas(11.4, (8.4, 8.3))
    x = 5.5
    place(axes, x, 10.8, "Готов к итерации (r, k)", initial=True)
    transition(axes, x, 9.75, "MPI_Barrier — вход")
    place(axes, x, 8.7, "Ждёт в MPI_Barrier")
    transition(axes, x, 7.65, "Все процессы вошли")
    place(axes, x, 6.6, "Выход разрешён")
    transition(axes, x, 5.55, "MPI_Barrier — возврат")
    place(axes, x, 4.5, "Блоки готовы к сумме")
    transition(axes, x, 3.45, "MPI_Reduce / MPI_SUM\nподсеть на рисунке 2", width=3.7)
    place(axes, x, 2.4, "Измерение завершено")
    transition(axes, x, 1.35, "Следующая итерация")
    transition(axes, 9.6, 2.4, "Завершить цикл")
    place(axes, 9.6, 1.25, "Готов к MPI_Reduce\nс MPI_MAX", width=3.35)
    for top, bottom in zip((10.8, 9.75, 8.7, 7.65, 6.6, 5.55, 4.5),
                           (9.75, 8.7, 7.65, 6.6, 5.55, 4.5, 3.45)):
        arrow(axes, (x, top-.38), (x, bottom+.38))
    arrow(axes, (x, 3.07), (x, 2.78), "MPI_Wtime: стоп", label_position=(7.2, 2.94))
    arrow(axes, (x, 2.02), (x, 1.67), "k < 9", label_position=(6.25, 1.85))
    arrow(axes, (7.15, 2.4), (8.0, 2.4), "k = 9", label_position=(7.58, 2.68))
    arrow(axes, (9.6, 2.08), (9.6, 1.63))
    arrow(axes, (3.9, 1.35), (1.4, 1.35))
    arrow(axes, (1.4, 1.35), (1.4, 10.8))
    arrow(axes, (1.4, 10.8), (3.85, 10.8), "k + 1", label_position=(2.6, 11.05))
    axes.text(8.7, 7.65, "По одной метке\nот каждого ранга r", va="center", ha="center", fontsize=11)
    axes.text(8.65, 4.5, "MPI_Wtime: старт,\nзатем локальная сумма¹", va="center",
              ha="center", color=INK, fontsize=11)
    axes.text(0.35, 0.4, "¹ Только в опытах с фиксированным числом наборов.", fontsize=10)
    save(figure, "petri-cycle.png")


def draw_reduce():
    figure, axes = canvas(8.7, (8.4, 6.7))
    for x, rank in ((2.8, "Ранг 0"), (8.7, "Ранги r = 1, …, p−1")):
        axes.text(x, 8.35, rank, ha="center", va="center", color=INK,
                  fontsize=13, weight="bold")
        place(axes, x, 7.65, "Локальный набор готов")
        transition(axes, x, 6.55, "MPI_Reduce — вход")
        arrow(axes, (x, 7.27), (x, 6.87))
    place(axes, 1.65, 5.35, "Корень в вызове", width=2.85)
    place(axes, 4.6, 5.35, "Вклад 0", width=1.85)
    place(axes, 7.35, 5.35, "Вклад r", width=1.85)
    place(axes, 10, 5.35, "Ранг r в вызове", width=3)
    arrow(axes, (2.7, 6.23), (1.65, 5.73))
    arrow(axes, (3.0, 6.23), (4.6, 5.73))
    arrow(axes, (8.5, 6.23), (7.35, 5.73))
    arrow(axes, (9.0, 6.23), (10, 5.73))
    transition(axes, 5.9, 4.1, "MPI_SUM — сведение вкладов", width=4.35)
    arrow(axes, (4.6, 4.97), (5.35, 4.42))
    arrow(axes, (7.35, 4.97), (6.45, 4.42))
    place(axes, 5.9, 3.0, "Сумма готова")
    arrow(axes, (5.9, 3.78), (5.9, 3.38))
    transition(axes, 2.8, 1.8, "MPI_Reduce — возврат", width=3.5)
    transition(axes, 10, 1.8, "MPI_Reduce — возврат", width=3.5)
    arrow(axes, (1.65, 4.97), (2.38, 2.12), bend=.1)
    arrow(axes, (5.9, 2.62), (3.65, 2.12))
    arrow(axes, (10, 4.97), (10, 2.12), "Буфер ввода\nможно переиспользовать",
          label_position=(9.92, 3.75))
    place(axes, 2.8, .7, "Корень получил сумму", width=3.9)
    place(axes, 10, .7, "Ранг r завершил вызов", width=3.9)
    arrow(axes, (2.8, 1.48), (2.8, 1.08))
    arrow(axes, (10, 1.48), (10, 1.08))
    save(figure, "petri-reduce.png")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    draw_cycle()
    draw_reduce()
