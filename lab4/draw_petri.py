"""Сеть фрагмента lab4: один столбец из трёх процессов: Mermaid, PNG и SVG.

Коллективный переход охватывает целиком одну операцию группы.
Модель не описывает внутренние пересылки MPI или порядок локальных возвратов.
Показан успешный запуск; обработка ошибок и бенчмарк вне модели.
"""
from collections import deque
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

OUT = Path(__file__).resolve().parent / 'results'
INK, BLUE = '#172c40', '#275c90'
NODES, ARCS = {}, []


def node(key, kind, x, y, label, marked=False, width=.5):
    NODES[key] = dict(kind=kind, x=x, y=y, label=label, marked=marked, width=width)
    return key


def connect(*keys):
    ARCS.extend(zip(keys, keys[1:]))


def build():
    NODES.clear()
    ARCS.clear()
    node('Tscatter', 'T', 4, 5.5, 'MPI_Scatter: раздать по одному числу', width=9)
    for lane, rank in enumerate([0, 3, 6]):
        x, number = lane*4, 10+lane
        start = node(f'Pstart{rank}', 'P', x, 10, f'Процесс {rank}\nстолбец создан', True)
        action = 'MPI_Comm_rank\nmalloc; заполнить массив' if rank == 0 else 'MPI_Comm_rank'
        prep = node(f'Tprepare{rank}', 'T', x, 8.5, action)
        ready = node(f'Pready{rank}', 'P', x, 7,
                     'Массив [10, 11, 12]\nготов к раздаче' if rank == 0 else 'Готов принять\nодно число')
        got = node(f'Pgot{rank}', 'P', x, 4, f'Получено {number}')
        output = node(f'Tprint{rank}', 'T', x, 2.5, 'printf')
        end = node(f'Pend{rank}', 'P', x, 1, f'Число {number}\nвыведено')
        connect(start, prep, ready, 'Tscatter', got, output, end)


def check():
    """Полный обход маркировок именно этой конечной обычной P/T-сети."""
    places = [key for key, item in NODES.items() if item['kind'] == 'P']
    transitions = [key for key, item in NODES.items() if item['kind'] == 'T']
    index = {key: i for i, key in enumerate(places)}
    for source, target in ARCS:
        assert NODES[source]['kind'] != NODES[target]['kind'], (source, target)
    inputs = {t: [index[a] for a, b in ARCS if b == t] for t in transitions}
    outputs = {t: [index[b] for a, b in ARCS if a == t] for t in transitions}
    initial = tuple(int(NODES[key]['marked']) for key in places)
    terminal = tuple(int(key.startswith('Pend')) for key in places)
    seen, pending, dead = {initial}, deque([initial]), []
    while pending:
        marking = pending.popleft()
        assert sum(marking) == 3 and max(marking) <= 1
        enabled = [t for t in transitions if all(marking[i] for i in inputs[t])]
        if not enabled:
            dead.append(marking)
        for transition in enabled:
            new = list(marking)
            for i in inputs[transition]:
                new[i] -= 1
            for i in outputs[transition]:
                new[i] += 1
            new = tuple(new)
            if new not in seen:
                seen.add(new)
                pending.append(new)
    assert dead == [terminal], 'Найдена неожиданная конечная маркировка'
    print(f'Проверено {len(seen)} маркировок; 3 фишки сохраняются; единственная остановка — завершение фрагмента.')


def mermaid():
    lines = ['flowchart TD',
             '    %% Один столбец {0, 3, 6} при запуске main.c на 9 процессах.',
             '    %% MPI_Cart_create и MPI_Cart_sub уже выполнены. M0: Pstart0=Pstart3=Pstart6=1.',
             '    %% Общий переход не означает одновременного возврата из MPI.',
             '    classDef place fill:#fff,stroke:#172c40,stroke-width:2px,color:#172c40;',
             '    classDef transition fill:#275c90,stroke:#172c40,color:#fff;']
    for key, item in NODES.items():
        label = item['label'].replace('\n', '<br/>')
        if item['marked']:
            label += '<br/>•'
        if item['kind'] == 'P':
            lines.append(f'    {key}(("{label}")):::place')
        else:
            lines.append(f'    {key}["{label}"]:::transition')
    lines.extend(f'    {a} --> {b}' for a, b in ARCS)
    (OUT/'petri.mmd').write_text('\n'.join(lines)+'\n')


def draw():
    fig, ax = plt.subplots(figsize=(11, 10))
    ax.set(xlim=(-.7, 11.6), ylim=(.5, 10.5), aspect='equal')
    ax.axis('off')
    for a, b in ARCS:
        source, target = NODES[a], NODES[b]
        sx, sy, tx, ty = source['x'], source['y'], target['x'], target['y']
        # Для общей планки точки крепления расположены напротив позиций.
        if source['kind'] == 'T' and source['width'] > 1:
            sx = tx
        if target['kind'] == 'T' and target['width'] > 1:
            tx = sx
        sy -= .23 if source['kind'] == 'P' else .08
        ty += .23 if target['kind'] == 'P' else .08
        ax.annotate('', xy=(tx, ty), xytext=(sx, sy),
                    arrowprops=dict(arrowstyle='->', color='#526273', lw=1.3))
    for item in NODES.values():
        x, y, label = item['x'], item['y'], item['label']
        if item['kind'] == 'P':
            ax.add_patch(Circle((x, y), .23, fc='white', ec=INK, lw=1.6, zorder=3))
            if item['marked']:
                ax.plot(x, y, 'o', color=INK, ms=5, zorder=4)
            ax.text(x+.35, y, label, va='center', fontsize=10, color=INK)
        else:
            width = item['width']
            ax.add_patch(Rectangle((x-width/2, y-.08), width, .16, fc=BLUE, zorder=3))
            if width > 1:
                ax.text(x, y+.22, label, ha='center', va='bottom', fontsize=10,
                        color=INK, bbox=dict(facecolor='white', edgecolor='none', pad=1))
            else:
                ax.text(x+.4, y, label, va='center', fontsize=9.5, color=INK)
    for extension in ('png', 'svg'):
        fig.savefig(OUT/f'petri.{extension}', dpi=180, bbox_inches='tight', pad_inches=.15)
    plt.close(fig)


if __name__ == '__main__':
    OUT.mkdir(exist_ok=True)
    build()
    check()
    mermaid()
    draw()
