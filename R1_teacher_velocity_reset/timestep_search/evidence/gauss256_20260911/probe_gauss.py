"""256배 Gauss 한 단계·독립 CPU 단계 식·기하·에너지·끝 상태 비교."""
import json,sys,time,types,hashlib,zipfile
from pathlib import Path
import numpy as np
from wind3dgs.teacher import p3_shell as sm,p3_shell_kernels as kernels
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy,ShellStepFailed
from wind3dgs.teacher.p3_shell_gauss import gauss_step
from wind3dgs.teacher.p3_shell_bounds import P3ShellBounds
from wind3dgs.teacher.p3_shell_precision_state import save_checkpoint,split_array
from wind3dgs.evaluation.teacher_timestep_trial import decode_trace,read
from wind3dgs.evaluation.teacher_timestep_search import verify_runtime
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
with zipfile.ZipFile(out/'source.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for path in Path('code/wind3dgs').rglob('*.py'):archive.write(path,str(path.relative_to('code')))
(out/'probe.py').write_bytes(Path(__file__).read_bytes())
p=Path('experiments/artifacts/runs/teacher_timestep_search/20260911_target256_segments_v2');verify_runtime(p)
source=p.parent/'20260911_precision_segments_v3/trials/sub004/failure_prefix.npz'
with np.load(source) as z:trace=decode_trace(dict(z),'hi_lo_v1')
with np.load(p/'wind.npz') as z:wind=z['wind_m_s'][195]
s,environment=make_shell_stepper(32,device='cuda:0',backend='precision_hvp_graph');s.policy=ShellSolvePolicy(**read(p/'plan.json')['policy']);m=s.model;bounder=P3ShellBounds(m.reference)
state=s.state(displacement=trace['u_m'][0],velocity=trace['v_m_s'][0],time_s=trace['time_s'][0]);force=m.aerodynamic_force_displacement(state.displacement_m,state.velocity_m_s,wind)['force_n'];h=1/60
report={'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((out/'source.zip').read_bytes()).hexdigest(),'environment':environment,'input_time_s':state.time_s,'dt_s':h,'stages':2,'substeps':1,'multiplier':256,'training_eligible':False}
start=time.perf_counter();print('Gauss256 계산 시작',flush=True)
try:end,d=gauss_step(s,state,force,h)
except ShellStepFailed as error:
 report.update(status='numerical_failure',reason=error.reason,attempts=error.attempts,solve_s=time.perf_counter()-start)
 (out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report),flush=True);sys.exit(0)
report.update(status='passed',solve_s=time.perf_counter()-start);print('Gauss256 독립 검산 시작',flush=True)
U=d.pop('stage_u_m');V=d.pop('stage_v_m_s');acc=d.pop('stage_a_m_s2');dense=d.pop('dense_initial_derivative_m_s');controls=d.pop('position_controls_m')
hp=types.ModuleType('hp');exec(Path(kernels.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
def arr(v,shape,name):
 a=np.array(v,dtype=np.longdouble,copy=True);assert a.shape==shape;return a
fg=dict(sm.__dict__);fg.update(kernels=hp,_array=arr);f=types.FunctionType(sm.P3Shell.evaluate_displacement.__code__,fg);f.__kwdefaults__={'direction':None}
audit_start=time.perf_counter();ratios=[]
for u,a in zip(U,acc):
 elastic=f(m.reference,u);ma=m.mass@a;res=ma-elastic['force_n']-force
 limit=s.policy.force_atol_n+s.policy.force_rtol*max(np.linalg.norm(x[m.free]) for x in [ma,elastic['force_n'],force])
 ratios.append(float(np.linalg.norm(res[m.free])/limit))
r=np.sqrt(np.longdouble(3))/6;coef=np.array([[np.longdouble('.25'),np.longdouble('.25')-r],[np.longdouble('.25')+r,np.longdouble('.25')]])
uerr=float(np.max(abs(U-state.displacement_m-h*np.einsum('ij,jkc->ikc',coef,V))))
verr=float(np.max(abs(V-state.velocity_m_s-h*np.einsum('ij,jkc->ikc',coef,acc))))
end_uerr=float(np.max(abs(end.displacement_m-state.displacement_m-h*V.mean(axis=0))))
end_verr=float(np.max(abs(end.velocity_m_s-state.velocity_m_s-h*acc.mean(axis=0))))
bounds=bounder.interval(state.displacement_m,dense,end.displacement_m,h)
e0=f(m.reference,state.displacement_m);e1=f(m.reference,end.displacement_m)
work=float(np.sum(force*(end.displacement_m-state.displacement_m)));balance=e1['energy_j']+s.kinetic_energy(end.velocity_m_s)-e0['energy_j']-s.kinetic_energy(state.velocity_m_s)-work;ledger=abs(balance-d['energy_balance_residual_j'])
audit={'force_ratios':ratios,'stage_position_defect_m':uerr,'stage_velocity_defect_m_s':verr,'end_position_defect_m':end_uerr,'end_velocity_defect_m_s':end_verr,'energy_ledger_error_j':ledger,'geometry':bounds}
audit['passed']=max(ratios)<=1 and max(uerr,end_uerr)<=2e-14 and max(verr,end_verr)<=1e-12 and ledger<=3e-16+1e-8*abs(balance) and bounds['projected_gradient_upper']<1
if not audit['passed']:report['status']='audit_failure'
report.update(diagnostics=d,audit=audit,audit_s=time.perf_counter()-audit_start,end_time_s=end.time_s)
save_checkpoint(out/'endpoint.npz',end)
arrays={}
for key,x in [('stage_u',U),('stage_v',V),('stage_a',acc)]:arrays[key+'_hi'],arrays[key+'_lo']=split_array(x)
np.savez_compressed(out/'stages.npz',**arrays)
ref=p.parent/'20260911_target256_accuracy_refine_v1/sub32_step31.npz'
with np.load(ref) as z:
 comparison={}
 for key,x in [('u',end.displacement_m),('v',end.velocity_m_s)]:
  y=z[key+'_hi'].astype(np.longdouble)+z[key+'_lo'].astype(np.longdouble);delta=x-y
  comparison[key]=float(np.sqrt(np.sum(delta*(m.mass@delta))/np.sum(y*(m.mass@y))))
report['endpoint_relative_mass_l2']=comparison;report['reference_sha256']=hashlib.sha256(ref.read_bytes()).hexdigest()
(out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report),flush=True)
