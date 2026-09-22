"""완료된 rest-start/reset 진단 원본을 그림으로 정리하는 실험 전용 wrapper."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from wind3dgs.evaluation.teacher_p3_shell_validation import read_run


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run',type=Path,required=True)
    parser.add_argument('--verification',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists(): parser.error('그림 출력 경로는 새 이름을 사용하세요')
    m,t,c,r=read_run(args.run)
    audit=json.loads(args.verification.read_text())
    if (audit['run']!=args.run.name or not audit['verified']
            or audit['manifest_sha256']!=hashlib.sha256((args.run/'manifest.json').read_bytes()).hexdigest()
            or c['initial_curvature']!=0 or c['reset_frame'] is None):
        raise ValueError('동일 원본의 검산과 rest-start/reset 조건이 필요합니다')
    s=c['substeps'];k=c['reset_frame']*s
    diagnostics=json.loads((args.run/'step_diagnostics.json').read_text())['steps']
    with np.load(args.run/'reset_event.npz',allow_pickle=False) as z: event=dict(z)
    kinetic=np.array([.5*np.sum(v*(m.mass@v)) for v in t['v_m_s']])
    total=np.r_[0.,[step['energy_j'] for step in diagnostics]]
    total[k]-=float(event['removed_kinetic_j'])
    elastic=total-kinetic
    # 같은 reset 시각의 직전/직후를 모두 그린다. 임의의 선형 감소로 보이지 않게 한다.
    time_ms=np.insert(t['time_s']*1000,k,t['time_s'][k]*1000)
    kinetic=np.insert(kinetic,k,float(event['removed_kinetic_j']))
    total=np.insert(total,k,total[k]+float(event['removed_kinetic_j']))
    elastic=np.insert(elastic,k,elastic[k])
    work=np.insert(np.r_[0.,np.cumsum(t['work_j'])],k,np.sum(t['work_j'][:k]))
    plt.rcParams.update({'font.family':'Noto Sans CJK KR','axes.unicode_minus':False,
                         'font.size':10,'pdf.fonttype':42})
    fig,axes=plt.subplots(1,2,figsize=(11,4.2),layout='constrained')
    xy=np.column_stack((np.linspace(.25,1,151),np.full(151,.5)))
    P=m.moving_surface_map(xy)
    axes[0].plot([0,1],[0,0],color='.65',ls='--',label='rest')
    for frame,color in zip((1,2,3),('#0072B2','#D55E00','#009E73')):
        u=P@t['u_m'][frame*s]
        label=f'{frame/60*1000:.2f} ms'
        if frame==c['reset_frame']: label+=' (reset 전·후 같은 형상)'
        axes[0].plot(xy[:,0]+u[:,0],u[:,1]*100,color=color,label=label)
    axes[0].axvspan(0,.25,color='.9',zorder=-1)
    axes[0].set(xlabel='현재 x (m)',ylabel='평면 밖 변위 y (cm)',
                title='중앙 단면의 실제 P3 변형',xlim=(0,1))
    axes[0].legend(fontsize=8,loc='upper left')
    for values,label,color,style in ((kinetic,'운동 에너지','#0072B2','-'),
                                    (elastic,'탄성 에너지','#009E73','-'),
                                    (total,'총 기계 에너지','#D55E00','-'),
                                    (work,'누적 외력 일','.35','--')):
        axes[1].plot(time_ms,values,label=label,color=color,ls=style)
    axes[1].axvline(t['time_s'][k]*1000,color='.55',ls=':')
    axes[1].set(xlabel='시각 (ms)',ylabel='에너지 / 일 (J)',title='위치 유지·속도 0 개입과 에너지 장부')
    axes[1].text(.03,.94,f"reset 제거 에너지: {float(event['removed_kinetic_j']):.6f} J",
                 transform=axes[1].transAxes,va='top',fontsize=9)
    axes[1].legend(fontsize=8,loc='lower left')
    for ax in axes: ax.grid(alpha=.18)
    fig.suptitle(f"P3 유한 회전 수식 진단 · n{m.resolution}, sub{s}, 3 frame · 학습데이터 아님",
                 fontsize=12)
    args.output.mkdir(parents=True)
    for ext in ('png','pdf'): fig.savefig(args.output/('rest_reset_diagnostic.'+ext),dpi=180)
    plt.close(fig)
    provenance={'run':args.run.name,'manifest_sha256':audit['manifest_sha256'],
                'verification_sha256':hashlib.sha256(args.verification.read_bytes()).hexdigest(),
                'wrapper_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'training_eligible':False,'generated_training_samples':0,
                'scope':'P3 중앙 단면과 실제 저장 interval의 에너지 장부. 연속 운동이나 공간 수렴 판정 아님'}
    (args.output/'provenance.json').write_text(json.dumps(provenance,ensure_ascii=False,indent=2)+'\n')
    print('P3 reset 진단 그림 저장 완료',flush=True)


if __name__=='__main__': main()
