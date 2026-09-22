"""256배 큰 변형 실패를 현재 접선 행렬의 보조 풀이로 재검산한다."""
import sys,json,time,types,hashlib,functools
from dataclasses import asdict
from pathlib import Path
import numpy as np
from wind3dgs.teacher import p3_shell as sm,p3_shell_kernels as kernels,p3_shell_dynamics as dynamics
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.teacher.p3_shell_precision_state import save_checkpoint
from wind3dgs.teacher.p3_shell_bounds import P3ShellBounds
from wind3dgs.evaluation.teacher_timestep_trial import decode_trace,read
from wind3dgs.evaluation.teacher_timestep_search import verify_runtime
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
p=Path('experiments/artifacts/runs/teacher_timestep_search/20260911_precision_segments_v4');verify_runtime(p)
source=p.parent/'20260911_precision_segments_v3/trials/sub004/failure_prefix.npz'
with np.load(source,allow_pickle=False) as z:trace=decode_trace(dict(z),'hi_lo_v1')
with np.load(p/'wind.npz',allow_pickle=False) as z:wind=z['wind_m_s'][195]
s,environment=make_shell_stepper(32,device='cuda:0',backend='precision_hvp_graph');s.policy=dynamics.ShellSolvePolicy(**read(p/'plan.json')['policy']);base=s.policy;m=s.model;bounder=P3ShellBounds(m.reference)
initial=s.state(displacement=trace['u_m'][0],velocity=trace['v_m_s'][0],time_s=trace['time_s'][0]);force=m.aerodynamic_force_displacement(trace['u_m'][0],trace['v_m_s'][0],wind)['force_n']
hp=types.ModuleType('hp');exec(Path(kernels.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
def arr(v,shape,name):
 a=np.array(v,dtype=np.longdouble,copy=True);assert a.shape==shape;return a
fg=dict(sm.__dict__);fg.update(kernels=hp,_array=arr)
f=types.FunctionType(sm.P3Shell.evaluate_displacement.__code__,fg);f.__kwdefaults__={'direction':None}
import importlib.util
helper_path=Path('code/wind3dgs/teacher/p3_shell_colored_preconditioner.py')
spec=importlib.util.spec_from_file_location('colored_probe',helper_path);helper=importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
(out/'preconditioner_source.py').write_bytes(helper_path.read_bytes())
print('현재 행렬 복원 패턴 준비',flush=True)
coloring=helper.ColoredPreconditioner(s.K);preconditioner_reports=[]
print('색 묶음 수: '+str(len(coloring.groups)),flush=True)
original_gmres=dynamics.gmres
@functools.wraps(original_gmres)
def logged_gmres(*a,**kw):
 kw['restart']=min(trial_restart,len(a[1]));kw['maxiter']=720//trial_restart
 kw['M'],info=coloring.build(a[0]);preconditioner_reports.append(info);print(json.dumps(info),flush=True)
 start=time.perf_counter();print('선형 풀이 시작',flush=True);r=original_gmres(*a,**kw);print('선형 풀이 종료: '+str(round(time.perf_counter()-start,3))+'초, info='+str(r[1]),flush=True);return r
dynamics.gmres=logged_gmres
report={'input_time_s':initial.time_s,'target_time_s':initial.time_s+1/60,'frame':195,'environment':environment,'policy':asdict(base),'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'runtime_manifest_sha256':hashlib.sha256((p/'runtime_manifest.json').read_bytes()).hexdigest(),'preconditioner_reports':preconditioner_reports,'helper_sha256':hashlib.sha256(helper_path.read_bytes()).hexdigest(),'trials':[],'training_eligible':False,'r1_complete':False}
for trial_restart in [240]:
 sub=1
 state=initial;dt=1/(60*sub);trial={'substeps':sub,'restart':trial_restart,'max_cycles':720//trial_restart,'max_iterations':720,'dt_s':dt,'rows':[],'status':'passed'}
 for index in range(1):
  start=time.perf_counter();print(f'분할{sub}, 시험 단계{index}',flush=True)
  try:end,d=s.step(state,force,dt)
  except dynamics.ShellStepFailed as error:
   trial.update(status='numerical_failure',reason=error.reason,attempts=error.attempts,failed_s=time.perf_counter()-start);break
  row={'index':index,'solve_s':time.perf_counter()-start,'attempts':d['attempts'],'hvp_calls':d['hvp_calls']}
  e0=f(m.reference,state.displacement_m);e1=f(m.reference,end.displacement_m);a0=np.zeros_like(state.displacement_m);a0[m.free]=s._solve_factor(s.mass_factor,(force+e0['force_n'])[m.free]);a1=2*(end.velocity_m_s-state.velocity_m_s)/dt-a0;ma=m.mass@a1;res=ma-e1['force_n']-force
  limit=base.force_atol_n+base.force_rtol*max(np.linalg.norm(x[m.free]) for x in [ma,force,e1['force_n']]);ratio=float(np.linalg.norm(res[m.free])/limit);update=float(np.max(abs(state.displacement_m+dt*state.velocity_m_s+dt*dt/4*(a0+a1)-end.displacement_m)))
  energy0=e0['energy_j']+s.kinetic_energy(state.velocity_m_s);energy1=e1['energy_j']+s.kinetic_energy(end.velocity_m_s);work=float(np.sum(force*(end.displacement_m-state.displacement_m)));balance=energy1-energy0-work;ledger=abs(balance-d['energy_balance_residual_j']);bounds=bounder.interval(state.displacement_m,state.velocity_m_s,end.displacement_m,dt)
  row['audit']={'residual_ratio':ratio,'position_update_error_m':update,'energy_ledger_error_j':ledger,'projected_gradient_upper':bounds['projected_gradient_upper']};row['audit_passed']=ratio<=1 and update<=2e-14 and ledger<=3e-16+1e-8*abs(balance) and bounds['projected_gradient_upper']<1
  trial['rows'].append(row);save_checkpoint(out/f'restart{trial_restart}_step{index}.npz',end);state=end
  if not row['audit_passed']:trial['status']='audit_failure';break
 trial['end_time_s']=state.time_s;trial['completed_solve_s']=sum(x['solve_s'] for x in trial['rows']);report['trials'].append(trial)
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(trial),flush=True)
