"""Run real MPI experiments; preserve logs, CSV and timing plots."""
import csv, os, re, subprocess, statistics
from pathlib import Path
os.chdir(Path(__file__).resolve().parent)
os.environ.setdefault('MPLCONFIGDIR', '/tmp/spod-mpl')
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
subprocess.run(['make','benchmark'], check=True)
Path('results').mkdir(exist_ok=True)
rows=[]
with open('results/runs.txt','w') as log:
    for mode in ['unordered','ordered']:
        for n in [1,1024,65536]:
            for p in [1,2,4,8,16,32]:
                times=[]
                for trial in range(7):
                    cmd=['mpirun','--oversubscribe','--bind-to','none','-np',str(p),'./benchmark',mode,str(n)]
                    text=subprocess.check_output(cmd,text=True,timeout=60)
                    log.write(' '.join(cmd)+'\n'+text+'\n')
                    ranks=list(map(int,re.search(r'ranks:([^\n]*)',text)[1].split()))
                    assert sorted(ranks)==list(range(p)), text
                    if mode=='ordered': assert ranks==list(range(p)),text
                    times.append(float(re.search(r'seconds=(\S+)',text)[1]))
                rows.append(dict(mode=mode,n=n,p=p,seconds=statistics.median(times)))
with open('results/timing.csv','w') as f:
    w=csv.DictWriter(f,fieldnames=['mode','n','p','seconds']);w.writeheader();w.writerows(rows)
for mode in ['unordered','ordered']:
    plt.figure()
    for n in [1,1024,65536]:
        subset=[r for r in rows if r['mode']==mode and r['n']==n]
        plt.plot([r['p'] for r in subset],[r['seconds']*1e6 for r in subset],'-o',label=f'n={n}')
    plt.xlabel('Processes');plt.ylabel('Time, microseconds');plt.legend();plt.grid();plt.tight_layout()
    plt.savefig(f'results/{mode}.png');plt.close()
print('Measurements saved. Update report with actual results before submitting.')
