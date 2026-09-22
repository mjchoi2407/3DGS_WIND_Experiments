"""각 시간 간격의 원래 실패 지점에서 최대2개 interval을 검산한다."""
import json,time,types,sys,hashlib,zipfile
from pathlib import Path
import numpy as np
from wind3dgs.teacher import p3_shell as shellmod,p3_shell_kernels as kernels
from wind3dgs.teacher.p3_shell_warp_precision import P3ShellWarpPrecision,P3ShellWarpPrecisionStepper
from wind3dgs.teacher.p3_shell_precision_state import split_array
from wind3dgs.teacher.p3_shell_dynamics import ShellStepFailed
from wind3dgs.teacher.p3_shell_bounds import P3ShellBounds
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
hp=types.ModuleType('hp');exec(Path(kernels.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
def arr(v,shape,name):
 a=np.array(v,dtype=np.longdouble,copy=True);assert a.shape==shape;return a
fg=dict(shellmod.__dict__);fg.update(kernels=hp,_array=arr)
f=types.FunctionType(shellmod.P3Shell.evaluate_displacement.__code__,fg);f.__kwdefaults__={'direction':None}
m=P3ShellWarpPrecision(shellmod.P3Shell(32),device='cuda:0',capture=True);s=P3ShellWarpPrecisionStepper(m);bounder=P3ShellBounds(m.reference)
base=Path('experiments/artifacts/runs/teacher_timestep_search/ten_second_v1');wind=np.load(base/'wind.npz')['wind_m_s'];reports=[]
for sub in [1,4,16,64]:
 folder=base/f'trials/sub{sub:03d}';meta=json.loads((folder/'failure.json').read_text());z=np.load(folder/'failure_prefix.npz');dt=1/(60*sub)
 state=s.state(displacement=z['u_m'][-1],velocity=z['v_m_s'][-1],time_s=z['time_s'][-1]);frame=meta['frame'];index=meta['substep']
 force=m.aerodynamic_force_displacement(z['u_m'][0],z['v_m_s'][0],wind[frame])['force_n']
 r={'substeps':sub,'source_sha256':hashlib.sha256((folder/'failure_prefix.npz').read_bytes()).hexdigest(),'rows':[],'status':'passed'};U=[state.displacement_m];V=[state.velocity_m_s];T=[state.time_s]
 for _ in range(2):
  if index==sub:
   frame+=1;index=0;force=m.aerodynamic_force_displacement(state.displacement_m,state.velocity_m_s,wind[frame])['force_n']
  previous=state;start=time.perf_counter()
  try:state,d=s.step(state,force,dt)
  except ShellStepFailed as error:
   r.update(status='numerical_failure',reason=error.reason,attempts=error.attempts,frame=frame,substep=index);break
  seconds=time.perf_counter()-start
  e0=f(m.reference,previous.displacement_m);e1=f(m.reference,state.displacement_m)
  a0=np.zeros_like(previous.displacement_m);a0[m.free]=s._solve_factor(s.mass_factor,(force+e0['force_n'])[m.free]);a1=2*(state.velocity_m_s-previous.velocity_m_s)/dt-a0;ma=m.mass@a1;res=ma-e1['force_n']-force
  limit=s.policy.force_atol_n+s.policy.force_rtol*max(np.linalg.norm(x[m.free]) for x in [ma,e1['force_n'],force]);ratio=float(np.linalg.norm(res[m.free])/limit)
  update=float(np.max(abs(previous.displacement_m+dt*previous.velocity_m_s+dt*dt/4*(a0+a1)-state.displacement_m)))
  bounds=bounder.interval(previous.displacement_m,previous.velocity_m_s,state.displacement_m,dt)
  work=float(np.sum(force*(state.displacement_m-previous.displacement_m)));balance=e1['energy_j']+s.kinetic_energy(state.velocity_m_s)-e0['energy_j']-s.kinetic_energy(previous.velocity_m_s)-work
  ledger=abs(balance-d['energy_balance_residual_j'])
  row={'frame':frame,'substep':index,'solve_s':seconds,'residual_ratio':ratio,'update_error_m':update,'ledger_error_j':ledger,'projected_gradient_upper':bounds['projected_gradient_upper']}
  row['verified']=ratio<=1 and update<=2e-14 and ledger<=3e-16+1e-8*abs(balance) and bounds['projected_gradient_upper']<1
  r['rows'].append(row);U.append(state.displacement_m);V.append(state.velocity_m_s);T.append(state.time_s);index+=1
  if not row['verified']:r['status']='audit_failure';break
 uh,ul=split_array(U);vh,vl=split_array(V);np.savez_compressed(out/f'sub{sub:03d}.npz',u_hi=uh,u_lo=ul,v_hi=vh,v_lo=vl,time_s=T)
 reports.append(r);(out/'report.json').write_text(json.dumps(reports,indent=2)+'\n');print(json.dumps(r),flush=True)
with zipfile.ZipFile(out/'source.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for path in Path('code/wind3dgs').rglob('*.py'):archive.write(path,str(path.relative_to('code')))
