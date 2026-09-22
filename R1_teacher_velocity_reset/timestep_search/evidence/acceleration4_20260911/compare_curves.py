"""동일 격자 Newmark 수치 보간의 consistent-mass norm 차이 상한. 참해 인증 아님."""
import sys,json
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
p=Path(sys.argv[1]);report=json.loads((p/'report.json').read_text());m=P3Shell(32)
def load(path):
 with np.load(path,allow_pickle=False) as z:return tuple(z[k+'_hi'].astype(np.longdouble)+z[k+'_lo'].astype(np.longdouble) for k in ('u','v'))
initial=load(p.parent/'20260911_gauss256_stage4_v1/endpoint.npz')
trials={t['substeps']:t for t in report['trials'] if t['status']=='passed'}
paths={s:p for s in trials}
if len(sys.argv)>2:
 ref=Path(sys.argv[2]);other=json.loads((ref/'report.json').read_text())
 for t in other['trials']:
  if t['status']=='passed':trials[t['substeps']]=t;paths[t['substeps']]=ref
def norm(a):return float(np.sqrt(max(np.longdouble(0),np.sum(a*(m.mass@a))/m.density)))
def trace(sub):return [initial]+[load(paths[sub]/f'sub{sub}_step{i}.npz') for i in range(len(trials[sub]['rows']))]
def sample(t,sub,clock):
 x=clock*sub;i=min(int(x),len(t)-2);q=np.longdouble(x-i);dt=np.longdouble(1)/(60*sub)
 u,v=t[i];un,vn=t[i+1]
 return u+q*dt*v+q*q*(un-u-dt*v),(1-q)*v+q*vn
results=[]
for coarse in sorted(trials):
 fine=max(trials)
 if coarse==fine:continue
 a=trace(coarse);b=trace(fine);count=len(b)-1
 assert len(a)>1 and fine%coarse==0 and (len(a)-1)*fine==count*coarse, '같은 구간의 중첩 시간 격자가 필요합니다'
 upper={'u':0.,'v':0.,'delta_u':0.};lower=dict(upper)
 for j in range(count):
  samples=[]
  for q in (0.,.5,1.):
   av=sample(a,coarse,(j+q)/fine);bv=sample(b,fine,(j+q)/fine)
   samples.append(tuple(x-y for x,y in zip(av,bv)))
   for k,field in enumerate(('u','v')):lower[field]=max(lower[field],norm(bv[k]))
   lower['delta_u']=max(lower['delta_u'],norm(bv[0]-initial[0]))
  # u는 이차 Bernstein 제어점, v는 선형 끝점의 norm 상한.
  controls=[samples[0][0],2*samples[1][0]-(samples[0][0]+samples[2][0])/2,samples[2][0]]
  upper['u']=max(upper['u'],*(norm(x) for x in controls));upper['delta_u']=upper['u']
  upper['v']=max(upper['v'],norm(samples[0][1]),norm(samples[2][1]))
 results.append({'candidate_substeps':coarse,'reference_substeps':fine,'relative_upper':{k:upper[k]/max(lower[k],1e-15) for k in upper},'absolute_upper':upper,'reference_peak_lower':lower,'compute_s':trials[coarse]['completed_solve_s']})
out={'scope':'동일 짧은 구간의 Newmark 수치 보간 비교. 부동소수점 계산이며 참해/interval arithmetic 인증 아님.','comparisons':results,'trial_compute_s':{s:t['completed_solve_s'] for s,t in trials.items()}}
(p/'curve_comparison.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps(out,ensure_ascii=False))
