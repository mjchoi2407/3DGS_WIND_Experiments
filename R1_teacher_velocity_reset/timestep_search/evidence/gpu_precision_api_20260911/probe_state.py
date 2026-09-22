"""저장 형식 채택 전 고정밀 상태·힘의 별도 진단. 기존 raw와 코드는 수정하지 않는다."""
import json,time,types,sys,inspect,hashlib,zipfile
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import splu
from wind3dgs.teacher import p3_shell as shellmod,p3_shell_kernels as kernels,p3_shell_dynamics as dynamics
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
ld=np.longdouble
if np.finfo(ld).nmant<=np.finfo(float).nmant:raise RuntimeError('확장 가수가 있는 longdouble 환경이 필요합니다')
output=Path(sys.argv[1]);output.mkdir(parents=True,exist_ok=False)
hp=types.ModuleType('hp_kernels');exec(Path(kernels.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
def arrayld(value,shape,name):
 a=np.array(value,dtype=ld,copy=True)
 if a.shape!=shape or not np.isfinite(a).all():raise ValueError(name)
 return a
force_globals=dict(shellmod.__dict__);force_globals.update(kernels=hp,_array=arrayld)
force_function=types.FunctionType(shellmod.P3Shell.evaluate_displacement.__code__,force_globals);force_function.__kwdefaults__={'direction':None}
class HighPrecisionModel:
 def __init__(self,base):self.base=base;self.reference=base.reference;self.calls=0;self.seconds=0.
 def __getattr__(self,key):return getattr(self.reference,key)
 def evaluate_displacement(self,u,*,direction=None):
  if direction is not None:return self.base.evaluate_displacement(np.asarray(u,dtype=float),direction=np.asarray(direction,dtype=float))
  start=time.perf_counter();r=force_function(self,u);self.calls+=1;self.seconds+=time.perf_counter()-start;return r
class FloatFactor:
 def __init__(self,base):self.base=base
 def solve(self,rhs):return self.base.solve(np.asarray(rhs,dtype=float))
def state128(u,v,t):
 arrays=[np.array(x,dtype=ld,copy=True) for x in (u,v)]
 for x in arrays:x.setflags(write=False)
 return dynamics.ShellState(*arrays,float(t))

s,env=make_shell_stepper(32,device='cuda:0',backend='hvp_graph');original_model=s.model;cpu_reference=HighPrecisionModel(original_model);
from wind3dgs.teacher.p3_shell_warp_precision import P3ShellWarpPrecision,P3ShellWarpPrecisionStepper
from wind3dgs.teacher.p3_shell_precision_state import save_checkpoint,load_checkpoint
from wind3dgs.teacher.p3_shell_bounds import P3ShellBounds
from wind3dgs.teacher.p3_shell_warp_fast import _HVPOnlyModel
s=P3ShellWarpPrecisionStepper(P3ShellWarpPrecision(original_model.reference,device="cuda:0",capture=True));bounder=P3ShellBounds(original_model.reference)
p=Path('experiments/artifacts/runs/teacher_timestep_search/20260911_incremental_newton_v1');z=np.load(p/'sub016.npz');wind=np.load(p.parent/'ten_second_v1/wind.npz')['wind_m_s'];force=original_model.aerodynamic_force_displacement(z['u_m'][-3],z['v_m_s'][-3],wind[160])['force_n'];state=s.state(displacement=z['u_m'][-1],velocity=z['v_m_s'][-1],time_s=z['time_s'][-1]);dt=1/(60*16);initial=state;rows=[];U=[state.displacement_m];V=[state.velocity_m_s];T=[state.time_s];start=time.perf_counter()
for step in range(2,10):
 previous=state;begin=time.perf_counter()
 try:state,d=s.step(state,force,dt)
 except dynamics.ShellStepFailed as e:
  rows.append({'substep':step,'status':e.reason,'attempts':e.attempts});break
 # 고정밀 식과 float64로 내린 기존 식을 각각 저장 상태에서 재계산한다.
 audits={}
 for mode,model,dtype in [('extended',cpu_reference,ld),('float64_export',original_model,float)]:
  u0=np.asarray(previous.displacement_m,dtype=dtype);v0=np.asarray(previous.velocity_m_s,dtype=dtype);u1=np.asarray(state.displacement_m,dtype=dtype);v1=np.asarray(state.velocity_m_s,dtype=dtype)
  e0=model.evaluate_displacement(u0);e1=model.evaluate_displacement(u1);a0=np.zeros_like(u0);a0[model.free]=s._solve_factor(s.mass_factor,(force+e0['force_n'])[model.free]);a1=2*(v1-v0)/dt-a0;ma=model.mass@a1;res=ma-e1['force_n']-force;limit=s.policy.force_atol_n+s.policy.force_rtol*max(np.linalg.norm(x[model.free]) for x in [ma,force,e1['force_n']]);audits[mode]={'residual_n':float(np.linalg.norm(res[model.free])),'limit_n':float(limit),'ratio':float(np.linalg.norm(res[model.free])/limit),'position_update_error_m':float(abs(u0+dt*v0+dt*dt/4*(a0+a1)-u1).max())}
 energy0=force_function(original_model.reference,previous.displacement_m)['energy_j']+s.kinetic_energy(previous.velocity_m_s)
 energy1=force_function(original_model.reference,state.displacement_m)['energy_j']+s.kinetic_energy(state.velocity_m_s)
 work=float(np.sum(force*(state.displacement_m-previous.displacement_m)))
 ledger_error=energy1-energy0-work-d['energy_balance_residual_j']
 bounds=bounder.interval(previous.displacement_m,previous.velocity_m_s,state.displacement_m,dt)
 assert audits['extended']['ratio']<=1 and audits['extended']['position_update_error_m']<=2e-14
 assert abs(ledger_error)<=3e-16
 assert bounds['projected_gradient_upper']<1
 row={'ledger_error_j':ledger_error,'projected_gradient_upper':bounds['projected_gradient_upper'],'substep':step,'status':'passed','newton_corrections':d['newton_corrections'],'elapsed_with_audit_s':time.perf_counter()-begin,'audits':audits};rows.append(row);U.append(state.displacement_m);V.append(state.velocity_m_s);T.append(state.time_s);print(json.dumps(row),flush=True)
# longdouble의 padding byte 대신 float64 hi/lo로 진단 원본을 보존한다.
arrays={}
for key,values in [('u',np.asarray(U)),('v',np.asarray(V))]:
 hi=values.astype(float);lo=(values-hi.astype(ld)).astype(float);assert np.array_equal(hi.astype(ld)+lo.astype(ld),values);arrays[key+'_hi']=hi;arrays[key+'_lo']=lo
arrays['time_s']=np.array(T);np.savez_compressed(output/'states_hi_lo.npz',**arrays)
# 같은 초기 상태의 힘 평가를 각 경로 3회씩 순차 측정한다. 외부 GPU 부하는 통제하지 않았다.
force_cost={}
for name,model in [('float64_gpu',original_model),('extended_cpu',cpu_reference),('selective_gpu',s.model)]:
 model.evaluate_displacement(initial.displacement_m);begin=time.perf_counter()
 for _ in range(3):model.evaluate_displacement(initial.displacement_m)
 force_cost[name]=(time.perf_counter()-begin)/3
manifest={}
with zipfile.ZipFile(output/'source.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for path in Path('code/wind3dgs').rglob('*.py'):
  rel=str(path.relative_to('code'));data=path.read_bytes();manifest[rel]=hashlib.sha256(data).hexdigest();archive.writestr(rel,data)
report={'environment':env,'longdouble_mantissa_bits_including_hidden':int(np.finfo(ld).nmant+1),'policy':s.policy.__dict__,'scope':'상태는 CPU longdouble, 기하 누적은 GPU hi/lo, 나머지 힘과 HVP는 float64. 독립 CPU 고정밀 검산. 저장 형식 미채택 진단.','rows':rows,'elapsed_with_audit_s':time.perf_counter()-start,'force_evaluation_mean_s':force_cost,'force_eval_counts':cpu_reference.calls,'source_sha256':manifest,'training_eligible':False,'r1_complete':False,'input_npz_sha256':hashlib.sha256((p/'sub016.npz').read_bytes()).hexdigest()}
(output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'summary':[(r['substep'],r['status']) for r in rows],'force_evaluation_mean_s':force_cost}),flush=True)

# 명시적 API의 파일 저장 및 새 모델 재시작을 같은 입력으로 대조한다.
checkpoint=output/'checkpoint.npz';initial_restart=s.state(displacement=U[4],velocity=V[4],time_s=T[4]);save_checkpoint(checkpoint,initial_restart)
restored=load_checkpoint(checkpoint,s)
assert np.array_equal(restored.displacement_m,U[4]) and np.array_equal(restored.velocity_m_s,V[4])
replayed,_=s.step(restored,force,dt)
restart={'storage_exact':True,'u_max_difference_m':float(np.max(abs(replayed.displacement_m-U[5]))),'v_max_difference_m_s':float(np.max(abs(replayed.velocity_m_s-V[5]))),'time_exact':replayed.time_s==T[5]}
assert restart['u_max_difference_m']<=1e-16 and restart['v_max_difference_m_s']<=1e-12 and restart['time_exact']
(output/'restart_check.json').write_text(json.dumps(restart,indent=2)+'\n')
print(json.dumps(restart),flush=True)
