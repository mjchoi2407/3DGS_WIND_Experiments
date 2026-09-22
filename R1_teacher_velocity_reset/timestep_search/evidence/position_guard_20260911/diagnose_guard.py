import sys,json
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.evaluation.teacher_timestep_trial import decode_trace
from wind3dgs.teacher.p3_shell_dynamics import ShellStepFailed
p=Path('experiments/artifacts/runs/teacher_timestep_search/20260911_precision_segments_v1');folder=p/'trials/sub004'
s,env=make_shell_stepper(32,backend='precision_hvp_graph',device='cuda:0')
with np.load(folder/'failure_prefix.npz') as z:trace=decode_trace(dict(z),'hi_lo_v1')
with np.load(p/'wind.npz') as z:wind=z['wind_m_s'][1]
state=s.state(displacement=trace['u_m'][-1],velocity=trace['v_m_s'][-1],time_s=trace['time_s'][-1]);force=s.model.aerodynamic_force_displacement(trace['u_m'][0],trace['v_m_s'][0],wind)['force_n']
def tracer(frame,event,arg):
 if frame.f_code.co_name=='step' and event=='exception' and isinstance(arg[1],ShellStepFailed):
  l=frame.f_locals
  if 'roundoff' in l:
   error=l['update_error'];bound=l['roundoff'];mask=(error>bound)&l['free'][:,None];inds=np.argwhere(mask)
   print(json.dumps({'reason':arg[1].reason,'guard_violations':len(inds),'max_error_m':float(error.max()),'error_norm_m':float(np.linalg.norm(error[l['free']])),'correction_limit_m':float(l['correction_limit']),'first_violations':[{'node':int(i),'component':int(j),'error':float(error[i,j]),'bound':float(bound[i,j]),'u':float(l['u'][i,j]),'a':float(l['a'][i,j]),'a0':float(l['a0'][i,j])} for i,j in inds[:8]]}),flush=True)
   np.savez('/tmp/position_guard_state.npz',**{k:l[k] for k in ['u','u0','v0','a0','a','predictor','update_error','roundoff']})
 return tracer
sys.settrace(tracer)
try:s.step(state,force,1/240)
except ShellStepFailed:pass
finally:sys.settrace(None)
