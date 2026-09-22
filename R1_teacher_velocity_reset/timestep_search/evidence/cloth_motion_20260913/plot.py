"""저장 궤적의 큰 움직임과 비평면 굽힘을 비교하는 정적 그림."""
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np

base=Path(__file__).parent
font=FontProperties(fname='/usr/share/fonts/truetype/unfonts-core/UnDotum.ttf')
plt.rcParams['font.family']=font.get_name()
plt.rcParams['axes.unicode_minus']=False
fig,axes=plt.subplots(2,2,figsize=(12,7),sharex=True,constrained_layout=True)
for column,(name,label) in enumerate([('reference_rectangle','직사각형'),('handkerchief','손수건')]):
    result=json.loads((base/(name+'.json')).read_text())
    rows=result['trajectory_geometry'];t=np.array([r['time_s'] for r in rows])
    for key,text,color in [('rms_displacement_m','전체 변위 RMS','#2166ac'),
                           ('best_plane_rms_m','최적 평면에서 벗어난 거리 RMS','#d6604d')]:
        axes[0,column].plot(t,[100*r[key] for r in rows],label=text,color=color)
    axes[0,column].set_title(label)
    axes[0,column].set_ylabel('거리 (cm)');axes[0,column].legend(fontsize=9)
    axes[1,column].plot(t,[r['plane_tilt_deg'] for r in rows],color='#2166ac',label='전체 기울기')
    samples=result['original_state_details']
    axes[1,column].scatter([r['time_s'] for r in samples],[r['normal_spread_p95_deg'] for r in samples],
                           color='#d6604d',s=25,label='표면 방향의 퍼짐 (대표 시각, 95%)')
    axes[1,column].set_ylabel('각도 (도)');axes[1,column].set_xlabel('시간 (초)')
    axes[1,column].legend(fontsize=9)
for ax in axes.flat:ax.grid(alpha=.2);ax.set_xlim(0,10)
fig.suptitle('완료 궤적: 큰 전체 기울어짐과 상대적으로 작은 비평면 굽힘',fontsize=14)
fig.savefig(base/'motion_summary.png',dpi=160)
plt.close(fig)
