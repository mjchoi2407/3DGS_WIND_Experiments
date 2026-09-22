"""동일 실패 인근 입력의 지수 적분 후보. 전체 곡선 검증과 분리한 개발 진단."""
import json,sys,time,types,hashlib,zipfile
from pathlib import Path
from dataclasses import asdict
import numpy as np
from wind3dgs.teacher import p3_shell as sm,p3_shell_kernels as kernels
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy,ShellStepFailed
from wind3dgs.teacher.p3_shell_exponential import exponential_step,midpoint_exponential_step,path_exponential_step,gauss_exponential_step
from wind3dgs.teacher import p3_shell_exponential as exponential_module
original_phi_sum=exponential_module.phi_sum_action
def logged_phi_sum(*args,**kwargs):
 print(f"지수함수 작용 시작: 차수{sorted(args[1])}, 허수축 범위{kwargs.get('imaginary_radius')}",flush=True)
 result,info=original_phi_sum(*args,**kwargs)
 print(f"지수함수 작용 종료: {info}",flush=True)
 return result,info
exponential_module.phi_sum_action=logged_phi_sum
from wind3dgs.teacher.p3_shell_gauss import geometry_bound
from wind3dgs.teacher.p3_shell_bounds import P3ShellBounds
from wind3dgs.teacher.p3_shell_precision_state import save_checkpoint,split_array,load_checkpoint
from wind3dgs.evaluation.teacher_timestep_trial import read
from wind3dgs.evaluation.teacher_timestep_search import verify_runtime
def json_safe(value):
 if isinstance(value,np.ndarray):
  return {'shape':list(value.shape),'dtype':str(value.dtype),'all_finite':bool(np.isfinite(value).all())}
 if isinstance(value,np.generic):return float(value)
 if isinstance(value,dict):return {k:json_safe(v) for k,v in value.items()}
 if isinstance(value,(list,tuple)):return [json_safe(v) for v in value]
 return value
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False);substeps=int(sys.argv[2]) if len(sys.argv)>2 else 1
with zipfile.ZipFile(out/'source.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for path in Path('code/wind3dgs').rglob('*.py'):archive.write(path,str(path.relative_to('code')))
(out/'probe.py').write_bytes(Path(__file__).read_bytes())
p=Path('experiments/artifacts/runs/teacher_timestep_search/20260911_target256_segments_v2');verify_runtime(p)
source=p.parent/'20260911_gauss256_stage4_v1/endpoint.npz'
with np.load(p/'wind.npz') as z:wind=z['wind_m_s'][196]
s,environment=make_shell_stepper(32,device='cuda:0',backend='precision_hvp_graph');s.policy=ShellSolvePolicy(**read(p/'plan.json')['policy']);m=s.model;bounder=P3ShellBounds(m.reference)
state=load_checkpoint(source,s);force=m.aerodynamic_force_displacement(state.displacement_m,state.velocity_m_s,wind)['force_n'];h=1/(60*substeps)
method_name=sys.argv[3] if len(sys.argv)>3 else '3'
method_order=None if method_name in ('path','hybrid') else 2 if method_name=='midpoint' else int(method_name)
path_degree=int(sys.argv[5]) if len(sys.argv)>5 else 20
if method_name=='path' and substeps!=1:raise ValueError('현재 경로 보정 probe는 공통1구간 전용입니다')
action_backend=sys.argv[4] if len(sys.argv)>4 else 'taylor'
hp=types.ModuleType('hp');exec(Path(kernels.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
def arr(v,shape,name):
 a=np.array(v,dtype=np.longdouble,copy=True);assert a.shape==shape;return a
fg=dict(sm.__dict__);fg.update(kernels=hp,_array=arr);f=types.FunctionType(sm.P3Shell.evaluate_displacement.__code__,fg);f.__kwdefaults__={'direction':None}
report={'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((out/'source.zip').read_bytes()).hexdigest(),'wind_sha256':hashlib.sha256((p/'wind.npz').read_bytes()).hexdigest(),'runtime_manifest_sha256':hashlib.sha256((p/'runtime_manifest.json').read_bytes()).hexdigest(),'environment':environment,'policy':asdict(s.policy),'input_time_s':state.time_s,'dt_s':h,'order':method_order,'method':method_name,'action_backend':action_backend,'substeps':substeps,'multiplier':256/substeps,'training_eligible':False,'continuous_geometry_verified':False,'status':'development_complete','rows':[]}
for index in range(substeps):
 start=time.perf_counter();print(f'지수 적분 계산 시작: {index+1}/{substeps}',flush=True)
 try:
  if method_name=='hybrid':end,d=gauss_exponential_step(s,state,force,h,degree=path_degree,max_action_seconds=240.)
  elif method_name=='path':
   path_source=p.parent/'20260911_gauss256_stage6_followup_v1/stages.npz'
   with np.load(path_source) as z:controls=z['position_controls_hi'].astype(np.longdouble)+z['position_controls_lo'].astype(np.longdouble)
   report['path_source_sha256']=hashlib.sha256(path_source.read_bytes()).hexdigest()
   report['path_degree']=path_degree
   end,d=path_exponential_step(s,state,force,h,controls,degree=path_degree,max_action_seconds=240.)
  elif method_name=='midpoint':end,d=midpoint_exponential_step(s,state,force,h,max_action_seconds=180.,action_backend=action_backend)
  else:end,d=exponential_step(s,state,force,h,order=method_order,max_action_seconds=180.,action_backend=action_backend)
 except (ShellStepFailed,RuntimeError) as error:
  report.update(status='numerical_or_cost_failure',reason=getattr(error,'reason',str(error)),attempts=getattr(error,'attempts',[]),failed_s=time.perf_counter()-start);break
 row={'index':index,'solve_s':time.perf_counter()-start};print('지수 적분 독립 힘 평가 검산 시작',flush=True)
 arrays={}
 for key in ['predictor_u_m','predictor_v_m_s','nonlinear_force_n','displacement_increment_m','velocity_increment_m_s']:
  arrays[key]=d.pop(key)
 for key in ['midpoint_predictor_u_m','midpoint_predictor_v_m_s','anchor_u_m','gauss_stage_u_m','gauss_stage_v_m_s','gauss_stage_a_m_s2','gauss_position_controls_m']:
  if key in d:arrays[key]=d.pop(key)
 poses=[state.displacement_m,arrays['predictor_u_m'],end.displacement_m]
 for key in ['midpoint_predictor_u_m','anchor_u_m']:
  if key in arrays:poses.append(arrays[key])
 ratios=[]
 for u in poses:
  cpu=f(m.reference,u);gpu=m.evaluate_displacement(u)
  limit=s.policy.force_atol_n+s.policy.force_rtol*float(np.linalg.norm(cpu['force_n'][m.free]))
  ratios.append(float(np.linalg.norm((gpu['force_n']-cpu['force_n'])[m.free])/limit))
 e0=f(m.reference,state.displacement_m);e1=f(m.reference,end.displacement_m)
 work=np.sum(force*(end.displacement_m-state.displacement_m));balance=e1['energy_j']+s.kinetic_energy(end.velocity_m_s)-e0['energy_j']-s.kinetic_energy(state.velocity_m_s)-work
 ledger=float(abs(balance-d['energy_balance_residual_j']))
 bounds=[geometry_bound(bounder,u[None]) for u in poses]
 uerr=float(np.max(abs(end.displacement_m-state.displacement_m-arrays['displacement_increment_m'])))
 verr=float(np.max(abs(end.velocity_m_s-state.velocity_m_s-arrays['velocity_increment_m_s'])))
 audit={'position_update_error_m':uerr,'velocity_update_error_m_s':verr,'force_evaluation_ratios':ratios,'energy_ledger_error_j':ledger,'sampled_geometry':bounds,'scope':'힘 평가·질량 풀이·표본 기하·에너지 장부 검산. Newton 단계 방정식 잔차나 전체 시간 곡선 기하/정확도 인증 아님.'}
 audit['passed']=uerr<=2e-14 and verr<=1e-12 and max(ratios)<1 and ledger<=3e-16+1e-8*abs(float(balance)) and all(b['injectivity_sufficient_condition'] for b in bounds)
 if 'gauss_stage_u_m' in arrays:
  stage_ratios=[]
  for u,a in zip(arrays['gauss_stage_u_m'],arrays['gauss_stage_a_m_s2']):
   elastic=f(m.reference,u)['force_n'];ma=m.mass@a
   limit=s.policy.force_atol_n+s.policy.force_rtol*max(np.linalg.norm(x[m.free]) for x in [ma,elastic,force])
   stage_ratios.append(float(np.linalg.norm((ma-elastic-force)[m.free])/limit))
  audit['gauss_stage_force_ratios']=stage_ratios
  audit['passed']=audit['passed'] and max(stage_ratios)<=1

 row.update(diagnostics=d,audit=audit,end_time_s=end.time_s);report['rows'].append(row)
 dest=out/f'step{index}';dest.mkdir();save_checkpoint(dest/'endpoint.npz',end)
 encoded={}
 for key,value in arrays.items():encoded[key+'_hi'],encoded[key+'_lo']=split_array(value)
 np.savez_compressed(dest/'details.npz',**encoded)
 if not audit['passed']:report['status']='audit_failure';break
 state=end
report['end_time_s']=state.time_s
if report['status']=='development_complete':
 save_checkpoint(out/'endpoint.npz',state)
 ref=p.parent/'20260911_gauss256_followup_gaussref4_v1/step3/endpoint.npz'
 with np.load(ref) as z:
  comparison={}
  for key,x in [('u',state.displacement_m),('v',state.velocity_m_s)]:
   y=z[key+'_hi'].astype(np.longdouble)+z[key+'_lo'].astype(np.longdouble);delta=x-y
   comparison[key]=float(np.sqrt(np.sum(delta*(m.mass@delta))/np.sum(y*(m.mass@y))))
 report['endpoint_relative_mass_l2']=comparison
(out/'report.json').write_text(json.dumps(json_safe(report),ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':report['status'],'rows':len(report['rows']),'reason':report.get('reason'),'endpoint':report.get('endpoint_relative_mass_l2')}),flush=True)
