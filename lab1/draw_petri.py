"""Draw exact ordinary Petri nets for two senders; replace report figures."""
import os
os.environ.setdefault('MPLCONFIGDIR','/tmp/spod-mpl')
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Rectangle
from docx import Document
b=Path(__file__).resolve().parent
for ordered in [False,True]:
    fig,ax=plt.subplots(figsize=(14,9))
    ax.set_xlim(-1,13);ax.set_ylim(-1,9);ax.set_aspect('equal');ax.axis('off')
    positions={'Q0':(1,4),'Q1':(6,4),'Q2':(11,4),
               'R1':(3.5,7),'D1':(8.5,7),'R2':(3.5,1),'D2':(8.5,1)}
    labels={'Q0':'Получено 0 сообщений','Q1':'Получено 1 сообщение','Q2':'Получено 2 сообщения',
            'R1':'Процесс 1 готов','D1':'Сообщение 1 принято',
            'R2':'Процесс 2 готов','D2':'Сообщение 2 принято'}
    transitions=[(0,1),(1,2)] if ordered else [(0,1),(0,2),(1,1),(1,2)]
    for k,i in transitions:
        x=3.5+5*k;y=5.4 if i==1 else 2.6
        ax.add_patch(Rectangle((x-.15,y-.42),.3,.84,color='#275c90'))
        ax.text(x+.27,y,f'Приём от {i}\nпосле {k} сообщений',va='center',fontsize=10)
        for source,target in [(positions[f'Q{k}'],(x,y)),(positions[f'R{i}'],(x,y)),((x,y),positions[f'Q{k+1}']),((x,y),positions[f'D{i}'])]:
            # Clip the arrow to circle/transition boundaries approximately.
            dx=target[0]-source[0];dy=target[1]-source[1];length=(dx*dx+dy*dy)**.5
            start=(source[0]+.35*dx/length,source[1]+.35*dy/length)
            end=(target[0]-.35*dx/length,target[1]-.35*dy/length)
            ax.annotate('',xy=end,xytext=start,arrowprops=dict(arrowstyle='->',color='#526273',lw=1.4,connectionstyle='arc3,rad=.08'))
    for name,(x,y) in positions.items():
        ax.add_patch(Circle((x,y),.35,facecolor='white',edgecolor='#172c40',lw=1.7,zorder=5))
        if name in ['Q0','R1','R2']:ax.plot(x,y,'o',color='#172c40',markersize=6,zorder=6)
        ax.text(x,y+.6,labels[name],ha='center',fontsize=11)
        ax.text(x,y-.62,name,ha='center',fontsize=10,color='#526273')
    title='Упорядоченный приём' if ordered else 'Приём от любого процесса'
    ax.set_title(title+' — сеть Петри для трёх процессов',fontsize=17,pad=16)
    fig.savefig(b/f'results/petri_{ordered}.png',dpi=200,bbox_inches='tight');plt.close(fig)
# Update only the two images; keep existing experiment text and results intact.
p=b/'Отчет_СПОД_ПР1_Тимошенков.docx'
d=Document(p)
for shape,ordered in zip(list(d.inline_shapes)[-5:-3],[False,True]):
    relationship=shape._inline.graphic.graphicData.pic.blipFill.blip.embed
    d.part.related_parts[relationship]._blob=(b/f'results/petri_{ordered}.png').read_bytes()
d.save(p)
print('Updated Russian diagrams and Word report')
