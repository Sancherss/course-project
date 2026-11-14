#!/usr/bin/env python3
"""Explanatory figures grounded in the pinned FIDO2.pvl, not wire-format specifications."""
from pathlib import Path
import os
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.tools/matplotlib-cache'))
os.environ.setdefault('XDG_CACHE_HOME',str(ROOT/'.tools/cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT=ROOT/'report/figures';OUT.mkdir(exist_ok=True)

def save(fig,name):
    for suffix in ('png','svg'):fig.savefig(OUT/f'{name}.{suffix}',dpi=180,bbox_inches='tight')
    plt.close(fig)

fig,ax=plt.subplots(figsize=(11,3.5),layout='constrained');ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
boxes=[(.015,'RP\nReg_Server\nAuth_Server'),(.36,'FC\nReg_Client\nAuth_Client'),(.705,'FA\nReg_Authnr\nAuth_Authnr')]
for x,label in boxes:
    ax.add_patch(FancyBboxPatch((x,.40),.28,.37,boxstyle='round,pad=0.012',facecolor='#edf2f7',edgecolor='#33495f'))
    ax.text(x+.14,.585,label,ha='center',va='center',fontsize=16)
for left,right,label in [(.295,.36,'CR'),(.64,.705,'CA')]:
    ax.annotate('',xy=(right,.59),xytext=(left,.59),arrowprops={'arrowstyle':'<->','lw':1.6,'color':'#33495f'})
    ax.text((left+right)/2,.79,label,ha='center',fontsize=18,fontweight='bold')
ax.text(.5,.94,'Историческая модель: каналы между честными ролями приватны',ha='center',fontsize=18)
ax.text(.5,.18,'E1/E2 добавляют отдельные сеансы с публичным интерфейсом cP.\nИсходные честные сеансы и их приватные каналы сохраняются.',ha='center',va='center',fontsize=18)
save(fig,'architecture')

fig,ax=plt.subplots(figsize=(11,6),layout='constrained');ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
left,right=.14,.86
for x,label in [(left,'CTAP_Client'),(right,'CTAP_Authnr')]:
    ax.text(x,.89,label,ha='center',va='top',fontweight='bold',fontsize=18)
    ax.plot([x,x],[.20,.72],ls='--',color='#9da8b3',lw=1)
ax.text(left,.81,'new b;\nbG = pk(b,G)',ha='center',va='top',fontsize=14)
ax.text(right,.81,'new a, PinToken;\naG = pk(a,G)',ha='center',va='top',fontsize=14)
for y,forward,label in [(.66,True,'CTAP1(OK)'),(.53,False,'CTAP2(aG)'),(.40,True,'CTAP7(bG, senc(hash(PIN), SS))'),(.27,False,'CTAP8(senc(PinToken, SS))')]:
    start,end=(left,right) if forward else (right,left)
    ax.annotate('',xy=(end,y),xytext=(start,y),arrowprops={'arrowstyle':'->','lw':1.5,'color':'#244761'})
    ax.text(.5,y+.025,label,ha='center',va='bottom',fontsize=18)
ax.text(.5,.17,'SS = hash_s(associate(b,aG)) = hash_s(associate(a,bG))',ha='center',fontsize=16)
ax.text(.5,.07,'Authenticator сравнивает расшифрованный hash(PIN) с ожидаемым.\nПосле CTAP8 клиент расшифровывает токен и сохраняет Client_Token.',ha='center',fontsize=16)
ax.text(.5,.99,'Ветка getToken исходной символической библиотеки',ha='center',fontsize=18)
save(fig,'gettoken')
print(OUT)
