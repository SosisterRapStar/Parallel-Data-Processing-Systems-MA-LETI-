import subprocess,csv
from pathlib import Path
out=['n,p,seconds,minimum,correct']
for n in [10000,1000000,10000000]:
 for p in [1,2,4,8,16,32]:
  s=subprocess.check_output(['mpirun','--oversubscribe','-np',str(p),'./practical2/minimum',str(n)],text=True).strip();out.append(s);print(s,flush=True)
Path('practical2/results.csv').write_text('\n'.join(out)+'\n')
