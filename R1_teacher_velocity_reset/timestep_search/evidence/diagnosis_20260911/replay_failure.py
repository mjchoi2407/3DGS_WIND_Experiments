import sys,json,time
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.teacher.p3_shell_dynamics import ShellStepFailed
p=Path('experiments/artifacts/runs/teacher_timestep_search/ten_second_v1')
s,env=make_shell_stepper(32,device='cuda:0',backend='hvp_graph');m=s.model;ref=m.reference;free=m.free
with np.load(p/'wind.npz') as z: wind=z['wind_m_s'].copy()
for sub in [64,16,4]:
 folder=p/f'trials/sub{sub:03d}';failure=json.loads((folder/'failure.json').read_text())
 with np.load(folder/'failure_prefix.npz') as z: U=z['u_m'].copy();V=z['v_m_s'].copy();T=z['time_s'].copy()
 force=m.aerodynamic_force_displacement(U[0],V[0],wind[failure['frame']])['force_n']
 state=s.state(displacement=U[-1],velocity=V[-1],time_s=float(T[-1]));best={};calls=[0]
 def tracer(frame,event,arg):
  if frame.f_code.co_name=='evaluate' and frame.f_code.co_filename.endswith('p3_shell_dynamics.py'):
   def local(fr,ev,arg):
    if ev=='return' and isinstance(arg,tuple):
     u,e,r,n,l=arg;calls[0]+=1
     if n < best.get('norm',float('inf')):best.update(u=u.copy(),a=fr.f_locals['acceleration'].copy(),force=e['force_n'].copy(),residual=r.copy(),norm=n,limit=l)
    return local
   return local
  return None
 sys.settrace(tracer);start=time.perf_counter()
 try:
  st,diag=s.step(state,force,1/(60*sub));result={'status':'passed','last':diag['attempts'][-1]}
 except ShellStepFailed as e:result={'status':e.reason,'last':e.attempts[-1]}
 finally:sys.settrace(None)
 result.update(substeps=sub,elapsed_s=time.perf_counter()-start,evaluations=calls[0],best_residual=best['norm'],force_limit=best['limit'])
 cpu=ref.evaluate_displacement(best['u'])['force_n'];inertia=ref.mass@best['a'];r_cpu=inertia-cpu-force
 repeated=[m.evaluate_displacement(best['u'])['force_n'] for _ in range(3)]
 result.update(cpu_residual_n=float(np.linalg.norm(r_cpu[free])),cpu_gpu_force_difference_n=float(np.linalg.norm((cpu-best['force'])[free])),repeat_force_difference_n=[float(np.linalg.norm((x-best['force'])[free])) for x in repeated],force_norms=[float(np.linalg.norm(x[free])) for x in [inertia,cpu,force]])
 print(json.dumps(result),flush=True)
