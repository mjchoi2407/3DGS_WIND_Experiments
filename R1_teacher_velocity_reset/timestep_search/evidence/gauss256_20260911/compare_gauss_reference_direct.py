"""동일 입력에서 시작하는 국소 시간 곡선을 비교한다."""
import json,sys
from pathlib import Path
from math import comb
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_gauss import tableau,position_controls
base=Path('experiments/artifacts/runs/teacher_timestep_search');m=P3Shell(32);h=np.longdouble(1/60)
def load(path,prefix):
 with np.load(path) as z:return z[prefix+'_hi'].astype(np.longdouble)+z[prefix+'_lo'].astype(np.longdouble)
initial={k:load(base/'20260911_gauss256_stage4_v1/endpoint.npz',k) for k in ['u','v']}
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

def gauss(n):
 state=initial;curves=[]
 for i in range(n):
  folder=base/'20260911_gauss256_stage6_followup_v1' if n==1 else base/f'20260911_gauss256_followup_gaussref{n}_v1'/f'step{i}'
  V=load(folder/'stages.npz','stage_v');acc=load(folder/'stages.npz','stage_a')
  curves.append({'u':position_controls(state['u'],V,h/n,tableau(6)[4]),'v':position_controls(state['v'],acc,h/n,tableau(6)[4])})
  state={k:load(folder/'endpoint.npz',k) for k in ['u','v']}
 return curves
def newmark():
 curves=[];state=initial
 for i in range(128):
  end={k:load(base/'20260911_gauss256_followup_refine128_v1'/f'sub128_step{i}.npz',k) for k in ['u','v']}
  curves.append({'u':np.stack([state['u'],state['u']+h/256*state['v'],end['u']]),'v':np.stack([state['v'],end['v']])});state=end
 return curves
def compare(a,b):
 N=max(len(a),len(b));upper={k:0. for k in initial};lower=upper.copy()
 peaks={k:max(norm(x[k][j]) for x in b for j in [0,-1]) for k in initial}
 for i in range(N):
  for k in initial:
   seg=[]
   for curves in [a,b]:
    q=N//len(curves);seg.append(restrict(curves[i//q][k],LD(i%q)/q,LD(i%q+1)/q))
   degree=max(len(x) for x in seg)-1;delta=elevate(seg[0],degree)-elevate(seg[1],degree)
   for q in range(16):
    part=restrict(delta,LD(q)/16,LD(q+1)/16)
    upper[k]=max(upper[k],max(norm(x) for x in part));lower[k]=max(lower[k],norm(part[0]),norm(part[-1]))
 return {'relative_upper':{k:(upper[k]+1e-12*max(1.,peaks[k]))/max(peaks[k]-1e-12*max(1.,peaks[k]),1e-30) for k in initial},'relative_sampled_lower':{k:lower[k]/peaks[k] for k in initial}}
ref=gauss(int(sys.argv[2]));results={'gauss6_one_to_reference':compare(gauss(1),ref),'newmark128_to_reference':compare(newmark(),ref)}
if int(sys.argv[2])==4:results['gauss6_reference2_to4']=compare(gauss(2),ref)
report={'scope':'한 구간의 수치 곡선 비교. 독립 ODE 참해 인증과 누적 오차 판정은 아님.','results':results,'training_eligible':False}
Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results),flush=True)
