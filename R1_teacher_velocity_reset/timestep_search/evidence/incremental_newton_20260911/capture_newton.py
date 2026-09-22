import sys,json
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.teacher.p3_shell_dynamics import ShellStepFailed
p=Path('experiments/artifacts/runs/teacher_timestep_search/ten_second_v1')
s,_=make_shell_stepper(32,device='cuda:0',backend='hvp_graph');sub=64
with np.load(p/'trials/sub064/failure_prefix.npz') as z: U=z['u_m'].copy();V=z['v_m_s'].copy();T=z['time_s'].copy()
with np.load(p/'wind.npz') as z: wind=z['wind_m_s'][158].copy()
force=s.model.aerodynamic_force_displacement(U[0],V[0],wind)['force_n'];state=s.state(displacement=U[-1],velocity=V[-1],time_s=T[-1]);best={};last={}
def tracer(fr,ev,arg):
 if fr.f_code.co_filename.endswith('p3_shell_dynamics.py') and fr.f_code.co_name in ('step','evaluate'):
  def local(f,e,a):
   if e=='return' and f.f_code.co_name=='evaluate' and isinstance(a,tuple):
    u,elastic,residual,norm,limit=a
    if norm<best.get('norm',float('inf')):best.update(u=u.copy(),acceleration=f.f_locals['acceleration'].copy(),norm=norm,limit=limit,force=elastic['force_n'].copy())
   if e=='return' and f.f_code.co_name=='step':
    last.update({k:np.array(f.f_locals[k],copy=True) for k in ['u0','v0','a0','a','delta','dt','c']})
   return local
  return local
sys.settrace(tracer)
try:s.step(state,force,1/(60*sub))
except ShellStepFailed as e:print('재현:',e.reason,flush=True)
finally:sys.settrace(None)
np.savez('/tmp/wind3dgs_newton_state.npz',**last,best_u=best['u'],best_a=best['acceleration'],best_force=best['force'],force=force,best_norm=best['norm'],force_limit=best['limit'])
print('실제 수정 방향과 최선 상태 저장 완료',flush=True)
