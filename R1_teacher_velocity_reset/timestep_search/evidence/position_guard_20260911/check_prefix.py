"""실제 n32·바람 조건의 초기6 frame을 독립 고정밀 식으로 검산한다."""
import sys,json,types,hashlib
from argparse import Namespace
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import splu
from wind3dgs.evaluation.teacher_timestep_search import prepare
from wind3dgs.evaluation.teacher_timestep_trial import run_trial,load_frame,trial_dir
from wind3dgs.teacher import p3_shell as shellmod,p3_shell_kernels as kernels
from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy
p=Path(sys.argv[1]);args=Namespace(smoke=False,precision=True,resolution=32,device='cuda:0',segment_seconds=2.5,max_trials=None,step_timeout=None,trial_timeout=14400.,budget_hours=4.)
prepare(p,args);report=run_trial(p,4,6)
assert report['status']=='prefix_passed' and report['completed_frames']==6,report
hp=types.ModuleType('hp');exec(Path(kernels.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
def arr(v,shape,name):
 a=np.array(v,dtype=np.longdouble,copy=True);assert a.shape==shape;return a
fg=dict(shellmod.__dict__);fg.update(kernels=hp,_array=arr)
f=types.FunctionType(shellmod.P3Shell.evaluate_displacement.__code__,fg);f.__kwdefaults__={'direction':None}
m=shellmod.P3Shell(32);factor=splu(m.mass[m.free][:,m.free].tocsc());policy=ShellSolvePolicy();dt=1/240;rows=[]
for frame in range(6):
 z=load_frame(trial_dir(p,4),frame);u=z['u_m'];v=z['v_m_s'];force=z['held_force_n'];previous=f(m,u[0])
 for i in range(4):
  end=f(m,u[i+1]);a0=np.zeros_like(u[i]);a0[m.free]=factor.solve(np.asarray((force+previous['force_n'])[m.free],dtype=float));a1=2*(v[i+1]-v[i])/dt-a0;ma=m.mass@a1;res=ma-end['force_n']-force
  limit=policy.force_atol_n+policy.force_rtol*max(np.linalg.norm(x[m.free]) for x in [ma,force,end['force_n']]);ratio=float(np.linalg.norm(res[m.free])/limit);update=float(np.max(abs(u[i]+dt*v[i]+dt*dt/4*(a0+a1)-u[i+1])))
  work=float(np.sum(force*(u[i+1]-u[i])));energy0=previous['energy_j']+float(.5*np.sum(v[i]*(m.mass@v[i])));energy1=end['energy_j']+float(.5*np.sum(v[i+1]*(m.mass@v[i+1])));balance=energy1-energy0-work;ledger=abs(balance-z['energy_balance_j'][i])
  assert ratio<=1 and update<=2e-14 and ledger<=3e-16+1e-8*abs(balance),(frame,i,ratio,update,ledger)
  rows.append({'frame':frame,'substep':i,'residual_ratio':ratio,'position_update_error_m':update,'energy_ledger_error_j':ledger});previous=end
summary={'frames':6,'intervals':len(rows),'max_residual_ratio':max(x['residual_ratio'] for x in rows),'max_update_error_m':max(x['position_update_error_m'] for x in rows),'max_ledger_error_j':max(x['energy_ledger_error_j'] for x in rows),'rows':rows,'training_eligible':False,'r1_complete':False}
(p/'independent_audit.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
