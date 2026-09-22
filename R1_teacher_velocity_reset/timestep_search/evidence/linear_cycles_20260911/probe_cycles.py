"""실패한 한 interval에서 선형 반복 한도만 바꾸어 순차 비교한다."""
import sys,json,time,types,hashlib
from dataclasses import replace,asdict
from pathlib import Path
import numpy as np
from wind3dgs.teacher import p3_shell as sm,p3_shell_kernels as kernels,p3_shell_dynamics as dynamics
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.teacher.p3_shell_precision_state import save_checkpoint
from wind3dgs.teacher.p3_shell_bounds import P3ShellBounds
from wind3dgs.evaluation.teacher_timestep_trial import decode_trace
from wind3dgs.evaluation.teacher_timestep_search import verify_runtime
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
p=Path('experiments/artifacts/runs/teacher_timestep_search/20260911_precision_segments_v2');verify_runtime(p)
with np.load(p/'trials/sub004/failure_prefix.npz',allow_pickle=False) as z:trace=decode_trace(dict(z),'hi_lo_v1')
with np.load(p/'wind.npz',allow_pickle=False) as z:wind=z['wind_m_s'][161]
s,environment=make_shell_stepper(32,device='cuda:0',backend='precision_hvp_graph');base=s.policy;m=s.model
state=s.state(displacement=trace['u_m'][-1],velocity=trace['v_m_s'][-1],time_s=trace['time_s'][-1]);force=m.aerodynamic_force_displacement(trace['u_m'][0],trace['v_m_s'][0],wind)['force_n'];dt=1/240
hp=types.ModuleType('hp');exec(Path(kernels.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
def arr(v,shape,name):
 a=np.array(v,dtype=np.longdouble,copy=True);assert a.shape==shape;return a
fg=dict(sm.__dict__);fg.update(kernels=hp,_array=arr)
f=types.FunctionType(sm.P3Shell.evaluate_displacement.__code__,fg);f.__kwdefaults__={'direction':None}
original_gmres=dynamics.gmres
# 원래 함수 서명을 유지하여 solver의 rtol/tol 분기를 바꾸지 않는다.
import functools
@functools.wraps(original_gmres)
def logged_gmres(*a,**kw):
 start=time.perf_counter();print('선형 풀이 시작',flush=True);r=original_gmres(*a,**kw);print('선형 풀이 종료: '+str(round(time.perf_counter()-start,3))+'초, info='+str(r[1]),flush=True);return r
dynamics.gmres=logged_gmres
report={'input_time_s':state.time_s,'frame':161,'substep':3,'dt_s':dt,'environment':environment,'base_policy':asdict(base),'input_sha256':hashlib.sha256((p/'trials/sub004/failure_prefix.npz').read_bytes()).hexdigest(),'runtime_manifest_sha256':hashlib.sha256((p/'runtime_manifest.json').read_bytes()).hexdigest(),'trials':[],'training_eligible':False,'r1_complete':False}
for cycles in [8,12,16]:
 s.policy=replace(base,linear_cycles=cycles);start=time.perf_counter();print('반복 한도 시험: '+str(cycles),flush=True)
 try:
  end,d=s.step(state,force,dt)
 except dynamics.ShellStepFailed as error:
  r={'linear_cycles':cycles,'status':'numerical_failure','reason':error.reason,'attempts':error.attempts,'solve_s':time.perf_counter()-start}
 else:
  r={'linear_cycles':cycles,'status':'passed','attempts':d['attempts'],'solve_s':time.perf_counter()-start,'hvp_calls':d['hvp_calls']}
  e0=f(m.reference,state.displacement_m);e1=f(m.reference,end.displacement_m);a0=np.zeros_like(state.displacement_m);a0[m.free]=s._solve_factor(s.mass_factor,(force+e0['force_n'])[m.free]);a1=2*(end.velocity_m_s-state.velocity_m_s)/dt-a0;ma=m.mass@a1;res=ma-e1['force_n']-force
  limit=base.force_atol_n+base.force_rtol*max(np.linalg.norm(x[m.free]) for x in [ma,force,e1['force_n']]);ratio=float(np.linalg.norm(res[m.free])/limit);update=float(np.max(abs(state.displacement_m+dt*state.velocity_m_s+dt*dt/4*(a0+a1)-end.displacement_m)))
  energy0=e0['energy_j']+s.kinetic_energy(state.velocity_m_s);energy1=e1['energy_j']+s.kinetic_energy(end.velocity_m_s);work=float(np.sum(force*(end.displacement_m-state.displacement_m)));balance=energy1-energy0-work;ledger=abs(balance-d['energy_balance_residual_j']);bounds=P3ShellBounds(m.reference).interval(state.displacement_m,state.velocity_m_s,end.displacement_m,dt)
  r['audit']={'residual_ratio':ratio,'position_update_error_m':update,'energy_ledger_error_j':ledger,'projected_gradient_upper':bounds['projected_gradient_upper']}
  r['audit_passed']=ratio<=1 and update<=2e-14 and ledger<=3e-16+1e-8*abs(balance) and bounds['projected_gradient_upper']<1
  save_checkpoint(out/f'cycles{cycles}_state.npz',end)
 report['trials'].append(r);(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(r),flush=True)
 if r['status']=='passed':break
