"""실행 중 본 계산을 수정하지 않는 동일1frame의 내부 허용오차 개발 비교."""
import sys,json,time,hashlib,types,zipfile
from pathlib import Path
from dataclasses import asdict
import numpy as np
from wind3dgs.teacher import p3_shell as sm,p3_shell_kernels as kernels
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy,ShellStepFailed
from wind3dgs.teacher.p3_shell_adaptive_preconditioner import AdaptivePreconditionerStepper
from wind3dgs.teacher.p3_shell_inexact_newton import InnerSolveTolerance
from wind3dgs.teacher.p3_shell_bounds import P3ShellBounds
from wind3dgs.teacher.p3_shell_precision_state import save_checkpoint
from wind3dgs.evaluation.teacher_timestep_trial import read,load_frame,trial_dir
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
main=Path('experiments/artifacts/runs/teacher_timestep_search/20260911_adaptive4_segments_v2');plan=read(main/'plan.json');frame=90
r=read(trial_dir(main,64)/'report.json');assert r['completed_frames']>=frame
trace=load_frame(trial_dir(main,64),frame-1,r)
raw,env=make_shell_stepper(32,device='cuda:0',backend='precision_hvp_graph');raw.policy=ShellSolvePolicy(**plan['policy'])
m=raw.model;bounder=P3ShellBounds(m.reference)
initial=raw.state(displacement=trace['u_m'][-1],velocity=trace['v_m_s'][-1],time_s=float(trace['time_s'][-1]))
with np.load(main/'wind.npz',allow_pickle=False) as z:wind=z['wind_m_s'][frame]
force=m.aerodynamic_force_displacement(initial.displacement_m,initial.velocity_m_s,wind)['force_n']
save_checkpoint(out/'initial.npz',initial)
np.savez_compressed(out/'held_force.npz',force_n=force,wind_m_s=wind)
with zipfile.ZipFile(out/'source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in sorted(Path('code/wind3dgs').rglob('*.py')):z.write(p,str(p))
(out/'probe.py').write_bytes(Path(__file__).read_bytes())
hp=types.ModuleType('hp');exec(Path(kernels.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
def arr(v,shape,name):
 a=np.array(v,dtype=np.longdouble,copy=True);assert a.shape==shape;return a
fg=dict(sm.__dict__);fg.update(kernels=hp,_array=arr)
f=types.FunctionType(sm.P3Shell.evaluate_displacement.__code__,fg);f.__kwdefaults__={'direction':None}
report={'input_time_s':initial.time_s,'frame':frame,'dt_s':1/(60*64),'steps':64,'policy':asdict(raw.policy),'environment':env,'gpu_shared_with_main':True,'timing_is_controlled_benchmark':False,'trials':[], 'main_modified':False,'training_eligible':False,'r1_complete':False,'source_frame_sha256':hashlib.sha256((trial_dir(main,64)/'frames'/f'{frame-1:03d}.npz').read_bytes()).hexdigest()}
paths={}
def dump(): (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
for mode in ['strict','fixed8','ew','strict_repeat']:
 raw.preconditioners.clear()
 raw._linear_tolerance_controller=None if mode.startswith('strict') else InnerSolveTolerance('fixed' if mode=='fixed8' else 'ew')
 s=AdaptivePreconditionerStepper(raw,switch_iterations=32,rebuild_every=4)
 state=initial;U=[state.displacement_m];V=[state.velocity_m_s];rows=[];trial={'mode':mode,'status':'running','rows':rows,'solve_s':0.,'audit_s':0.};report['trials'].append(trial);folder=out/mode;folder.mkdir();dump()
 for i in range(64):
  start=time.perf_counter()
  try:end,d=s.step(state,force,report['dt_s'])
  except (ShellStepFailed,ValueError) as err:
   trial.update(status='numerical_failure',failed_step=i,reason=str(err),attempts=getattr(err,'attempts',[]),failed_s=time.perf_counter()-start);break
  elapsed=time.perf_counter()-start;trial['solve_s']+=elapsed;start=time.perf_counter()
  e0=f(m.reference,state.displacement_m);e1=f(m.reference,end.displacement_m);dt=report['dt_s'];a0=np.zeros_like(state.displacement_m);a0[m.free]=s._solve_factor(s.mass_factor,(force+e0['force_n'])[m.free]);a1=2*(end.velocity_m_s-state.velocity_m_s)/dt-a0;ma=m.mass@a1;res=ma-e1['force_n']-force
  limit=raw.policy.force_atol_n+raw.policy.force_rtol*max(np.linalg.norm(x[m.free]) for x in [ma,force,e1['force_n']]);ratio=float(np.linalg.norm(res[m.free])/limit);update=float(np.max(abs(state.displacement_m+dt*state.velocity_m_s+dt*dt/4*(a0+a1)-end.displacement_m)))
  energy0=e0['energy_j']+s.kinetic_energy(state.velocity_m_s);energy1=e1['energy_j']+s.kinetic_energy(end.velocity_m_s);work=float(np.sum(force*(end.displacement_m-state.displacement_m)));balance=energy1-energy0-work;ledger=float(abs(balance-d['energy_balance_residual_j']));bounds=bounder.interval(state.displacement_m,state.velocity_m_s,end.displacement_m,dt)
  passed=ratio<=1 and update<=2e-14 and ledger<=3e-16+1e-8*abs(balance) and bounds['projected_gradient_upper']<1
  rows.append({'step':i,'solve_s':elapsed,'attempts':d['attempts'],'newton_corrections':d['newton_corrections'],'hvp_calls':d['hvp_calls'],'adaptive':d['adaptive_preconditioner'],'force_ratio':ratio,'position_update_error_m':update,'energy_ledger_error_j':ledger,'projected_gradient_upper':bounds['projected_gradient_upper'],'audit_passed':bool(passed)})
  trial['audit_s']+=time.perf_counter()-start;state=end;U.append(state.displacement_m);V.append(state.velocity_m_s)
  if not passed:trial.update(status='audit_failure',failed_step=i);break
  if i%8==0: print(f'{mode}: {i+1}/64 단계, 계산 {trial["solve_s"]:.2f}초',flush=True);dump()
 if len(rows)==64 and all(x['audit_passed'] for x in rows):trial['status']='passed'
 trial['completed_steps']=len(rows);save_checkpoint(folder/'endpoint.npz',state);paths[mode]=(U,V)
 for key,data in [('u',U),('v',V)]:
  a=np.asarray(data,dtype=np.longdouble);hi=np.asarray(a,dtype=np.float64);np.savez_compressed(folder/f'{key}_path.npz',hi=hi,lo=np.asarray(a-hi.astype(np.longdouble),dtype=np.float64))
 dump();print(mode,trial['status'],round(trial['solve_s'],3),flush=True)
# 같은 시간 격자의 이차 위치/선형 속도 수치 보간 비교.
def norm(x):return float(np.sqrt(max(0,np.sum(x*(m.mass@x))/m.density)))
comparisons={};reference=paths['strict']
if len(reference[0])==65:
 for mode,(U,V) in paths.items():
  if len(U)!=65:continue
  du=[a-b for a,b in zip(U,reference[0])];dv=[a-b for a,b in zip(V,reference[1])]
  upper_u=max([norm(x) for x in du]+[norm(du[i]+.5*report['dt_s']*dv[i]) for i in range(64)])
  comparisons[mode]={'u_relative_upper':upper_u/max(max(norm(x) for x in reference[0]),1e-15),'v_relative_upper':max(norm(x) for x in dv)/max(max(norm(x) for x in reference[1]),1e-15),'max_u_difference_m':max(float(np.max(abs(x))) for x in du),'max_v_difference_m_s':max(float(np.max(abs(x))) for x in dv)}
report['same_dt_curve_comparisons']=comparisons;dump()
