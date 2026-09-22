"""공통1/60초 구간의 Bernstein 차이 control로 전체 시간 L2 상한을 비교한다."""
import json,sys
from pathlib import Path
from math import comb
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_gauss import tableau,position_controls
from wind3dgs.evaluation.teacher_timestep_trial import decode_trace
base=Path('experiments/artifacts/runs/teacher_timestep_search');m=P3Shell(32);h=np.longdouble(1/60)
with np.load(base/'20260911_precision_segments_v3/trials/sub004/failure_prefix.npz') as z:
 t=decode_trace(dict(z),'hi_lo_v1');initial={'u':t['u_m'][0],'v':t['v_m_s'][0]}
def load_state(path):
 with np.load(path) as z:return {k:z[k+'_hi'].astype(np.longdouble)+z[k+'_lo'].astype(np.longdouble) for k in ['u','v']}
refs={}
for n,folder in [(16,'20260911_target256_accuracy_reference_v1'),(32,'20260911_target256_accuracy_refine_v1')]:
 refs[n]=[initial]+[load_state(base/folder/f'sub{n}_step{i}.npz') for i in range(n)]
def norm(x):return float(np.sqrt(max(np.sum(x*(m.mass@x)),0)))
def split(ctrl,t):
 layers=[ctrl]
 while len(layers[-1])>1:layers.append((1-t)*layers[-1][:-1]+t*layers[-1][1:])
 return np.stack([x[0] for x in layers]),np.stack([x[-1] for x in layers[::-1]])
def restrict(ctrl,a,b):
 left=split(ctrl,b)[0]
 return split(left,a/b)[1] if a else left

def elevate(ctrl,n):
 p=len(ctrl)-1
 return np.stack([sum(LD(comb(p,i)*comb(n-p,j-i))/comb(n,j)*ctrl[i] for i in range(max(0,j-(n-p)),min(p,j)+1)) for j in range(n+1)])
LD=np.longdouble
refctrl=[]
for a,b in zip(refs[32][:-1],refs[32][1:]):refctrl.append({'u':np.stack([a['u'],a['u']+h/64*a['v'],b['u']]),'v':np.stack([a['v'],b['v']])})
peaks={k:max(norm(x[k]) for x in refs[32]) for k in ['u','v']}
results={}
for stages in [2,3,4,6]:
 folder=base/('20260911_gauss256_v1' if stages==2 else f'20260911_gauss256_stage{stages}_v1')
 if not (folder/'stages.npz').exists():continue
 with np.load(folder/'stages.npz') as z:
  W=z['stage_v_hi'].astype(LD)+z['stage_v_lo'].astype(LD);acc=z['stage_a_hi'].astype(LD)+z['stage_a_lo'].astype(LD)
 powers=tableau(stages)[4]
 controls={'u':position_controls(initial['u'],W,h,powers),'v':position_controls(initial['v'],acc,h,powers)}
 upper={k:0. for k in peaks};sampled={k:0. for k in peaks}
 for j,fine in enumerate(refctrl):
  for k in peaks:
   coarse=restrict(controls[k],LD(j)/32,LD(j+1)/32)
   other=elevate(fine[k],stages);delta=coarse-other
   sampled[k]=max(sampled[k],norm(delta[0]),norm(delta[-1]))
   for q in range(4):upper[k]=max(upper[k],max(norm(x) for x in restrict(delta,LD(q)/4,LD(q+1)/4)))
 derivative=stages*np.diff(controls['u'],axis=0)/h
 defect=elevate(derivative,stages)-controls['v']
 # 부동소수 연산 여유. 경계에 가까운 판정은 추가 세분/독립 확인이 필요하다.
 relative={k:(upper[k]+1e-12*max(1.,peaks[k]))/max(peaks[k]-1e-12*max(1.,peaks[k]),1e-30) for k in peaks}
 results[f'gauss{stages}']={'relative_upper':relative,'relative_sampled_lower':{k:sampled[k]/peaks[k] for k in peaks},
                          'velocity_consistency_relative_upper':max(norm(x) for q in range(128) for x in restrict(defect,LD(q)/128,LD(q+1)/128))/peaks['v'],
                          'passed_local_one_percent':max(relative.values())<.01}
upper={k:0. for k in peaks}
for j,fine in enumerate(refctrl):
 a,b=refs[16][j//2:j//2+2]
 ctrls={'u':np.stack([a['u'],a['u']+h/32*a['v'],b['u']]),'v':np.stack([a['v'],b['v']])}
 for k in peaks:
  segment=restrict(ctrls[k],LD(j%2)/2,LD(j%2+1)/2);delta=segment-fine[k]
  for q in range(4):upper[k]=max(upper[k],max(norm(x) for x in restrict(delta,LD(q)/4,LD(q+1)/4)))
results['reference16_to32']={'relative_upper':{k:upper[k]/peaks[k] for k in peaks}}
report={'scope':'주어진 한 구간의 Gauss collocation 곡선 대32분할 Newmark 수치 곡선. Bernstein convex-hull L2 상한+명시적 부동소수 여유. 엄밀한 interval arithmetic 또는 독립 ODE 참해 인증 아님.', 'results':results,'training_eligible':False}
Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results),flush=True)
