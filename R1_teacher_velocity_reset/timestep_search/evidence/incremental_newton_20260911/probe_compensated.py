import inspect,textwrap,json,time
import numpy as np
from pathlib import Path
from wind3dgs.teacher import p3_shell_dynamics as dynamics
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
src=textwrap.dedent(inspect.getsource(dynamics.P3ShellStepper.step))
src=src.replace('last_correction=0.', 'u_comp=np.zeros_like(u)\n    last_correction=0.')
src=src.replace('trial_u=u+alpha*(c*delta)', 'increment=alpha*(c*delta)-u_comp\n                    trial_u=u+increment\n                    trial_comp=(trial_u-u)-increment')
src=src.replace('a+=alpha*delta; u=trial_u;', 'a+=alpha*delta; u=trial_u; u_comp=trial_comp;')
ns=dict(dynamics.__dict__);exec(src,ns);dynamics.P3ShellStepper.step=ns['step'];s,_=make_shell_stepper(32,device='cuda:0',backend='hvp_graph');p=Path('experiments/artifacts/runs/teacher_timestep_search/20260911_incremental_newton_v1');z=np.load(p/'sub016.npz');wind=np.load(p.parent/'ten_second_v1/wind.npz')['wind_m_s'];force=s.model.aerodynamic_force_displacement(z['u_m'][-3],z['v_m_s'][-3],wind[160])['force_n'];state=s.state(displacement=z['u_m'][-1],velocity=z['v_m_s'][-1],time_s=z['time_s'][-1]);results=[]
assert abs(float(z['time_s'][-3])-160/60)<1e-10
for i in range(2,6):
 try:
  state,d=s.step(state,force,1/(60*16));r={'substep':i,'status':'passed','last':d['attempts'][-1]}
 except dynamics.ShellStepFailed as e:r={'substep':i,'status':e.reason,'last':e.attempts[-1]}
 print(json.dumps(r),flush=True);results.append(r)
 if r['status']!='passed':break
Path('/tmp/wind3dgs_compensated_probe.json').write_text(json.dumps(results,indent=2)+'\n')
