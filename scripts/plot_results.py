#!/usr/bin/env python3
"""Export the twelve actual main-matrix outcomes; do not aggregate diagnostic false as attacks."""
from pathlib import Path
import json
import os
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.tools/matplotlib-cache'))
os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'.tools/cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

snapshot=ROOT/(ROOT/'evidence/final-summary-location.txt').read_text().strip()
rows=json.loads((snapshot/'summary.json').read_text())
lookup={r['experiment_id']:r for r in rows}
colors=['#d9e9df','#f5dacb','#e8e7ed']
values=[];labels=[]
for group in range(4):
    row=[];text=[]
    for index in range(3):
        result=lookup[f'R{group*3+index+1:02d}']
        row.append({'PROVED':0,'ATTACK_OR_FALSE':1,'UNKNOWN':2}[result['status']])
        reason='timeout' if result['timed_out'] else 'cannot be proved'
        text.append(result['status'] if result['status']=='PROVED' else ('FALSE + trace' if result['status']=='ATTACK_OR_FALSE' else 'UNKNOWN\n'+reason))
    values.append(row);labels.append(text)
fig,ax=plt.subplots(figsize=(11,4.9),layout='constrained')
ax.imshow(values,cmap=ListedColormap(colors),vmin=0,vmax=2,aspect='auto')
ax.set_xticks(range(3),['E0: original roles','E1: extra client\npublic CA','E2: extra client\npublic CR'])
ax.set_yticks(range(4),['Registration / S-pintok','Registration / A6','Authentication / S-pintok','Authentication / A1'])
for i in range(4):
    for j in range(3):ax.text(j,i,labels[i][j],ha='center',va='center',fontsize=16,color='#20242c')
ax.set_xticks([-.5,.5,1.5,2.5],minor=True);ax.set_yticks([-.5,.5,1.5,2.5,3.5],minor=True)
ax.grid(which='minor',color='white',linewidth=3);ax.tick_params(which='minor',bottom=False,left=False)
ax.tick_params(axis='both',length=0,pad=10,labelsize=16)
for spine in ax.spines.values():spine.set_visible(False)
ax.set_title('FIDO2Verif historical model: 12 controlled comparisons\nProVerif 2.05, getToken/client, default settings, 60 s limit',pad=20,fontsize=20)
fig.supxlabel('UNKNOWN is inconclusive. Results do not assess current FIDO2 implementations.',fontsize=16)
folder=ROOT/'report/figures';folder.mkdir(exist_ok=True)
for ext in ('png','svg'):fig.savefig(folder/f'matrix.{ext}',dpi=180)
plt.close(fig)
print(folder)
