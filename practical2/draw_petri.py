"""Сеть Петри поиска минимума: все позиции и переходы подписаны по-русски."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle

fig, ax = plt.subplots(figsize=(11, 12))
ax.set(xlim=(-1, 11), ylim=(-.7, 13.6))
ax.axis('off')
positions = {'Массив': (5, 12.8), 'Результат': (5, -.2)}
transitions = {'Раздать блоки': (5, 11.8), 'Выбрать общий минимум': (5, 1.3)}
labels = {'Массив': 'Исходный массив', 'Результат': 'Общий минимум'}
edges = [('Массив', 'Раздать блоки'), ('Выбрать общий минимум', 'Результат')]
for rank, x in enumerate([1, 5, 9]):
    for key, y, label in [('Б',10.6,'Блок подготовлен'), ('П',8.2,'Блок принят'),
                           ('Л',5.8,'Минимум найден'), ('К',3.4,'Минимум у корня')]:
        name = f'{key}{rank}'
        positions[name] = (x, y)
        labels[name] = f'{name}: {label}'
    for key, y, label in [('Приём',9.4,'Принять блок'), ('Поиск',7,'Найти минимум'),
                           ('Возврат',4.6,'Вернуть минимум')]:
        name = f'{key}{rank}'
        transitions[name] = (x, y)
        labels[name] = label
    if rank == 0:
        labels['Приём0'] = 'Скопировать свой блок'
        labels['Возврат0'] = 'Сохранить свой минимум'
    chain = ['Раздать блоки', f'Б{rank}', f'Приём{rank}', f'П{rank}',
             f'Поиск{rank}', f'Л{rank}', f'Возврат{rank}', f'К{rank}',
             'Выбрать общий минимум']
    edges.extend(zip(chain, chain[1:]))
    # Номер процесса указан в обозначениях позиций каждой ветви.
coords = positions | transitions
for source, target in edges:
    x, y = coords[source]; xx, yy = coords[target]
    dx, dy = xx-x, yy-y
    length = (dx*dx+dy*dy)**.5
    ax.annotate('', xy=(xx-.22*dx/length, yy-.22*dy/length),
                xytext=(x+.22*dx/length, y+.22*dy/length),
                arrowprops={'arrowstyle':'->','color':'#526273','lw':1.5})
for name, (x, y) in positions.items():
    ax.add_patch(Circle((x,y), .18, fc='white', ec='#172c40', lw=1.5, zorder=4))
    ax.text(x, y+.3, labels[name], ha='center', fontsize=11,
            bbox={'facecolor':'white','edgecolor':'none','pad':1})
    if name == 'Массив':
        ax.plot(x,y,'o',color='#172c40',markersize=5,zorder=5)
for name, (x,y) in transitions.items():
    ax.add_patch(Rectangle((x-.7,y-.14),1.4,.28,fc='#275c90',zorder=4))
    ax.text(x,y-.4,labels.get(name,name),ha='center',fontsize=11,
            bbox={'facecolor':'white','edgecolor':'none','pad':1})
ax.text(5, 13.4, 'Поиск минимума массива: три процесса', ha='center', fontsize=16, weight='bold')
fig.savefig(Path(__file__).parent/'petri.png', dpi=200, bbox_inches='tight')
