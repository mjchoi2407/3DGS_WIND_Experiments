import json,time,hashlib,zipfile,sys
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.teacher.p3_shell_dynamics import ShellStepFailed
from wind3dgs.teacher.p3_shell_bounds import P3ShellBounds
from wind3dgs.evaluation.teacher_p3_shell_random import sources,file_identity
out=Path(sys.argv[1]);out.mkdir(parents=True,exist_ok=False)
p=Path('experiments/artifacts/runs/teacher_timestep_search/ten_second_v1');wind=np.load(p/'wind.npz')['wind_m_s'];manifest=sources()
(out/'source_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
with zipfile.ZipFile(out/'source.zip','w',zipfile.ZIP_DEFLATED) as archive:
 for path in manifest:archive.write(Path('code')/path,path)
s,environment=make_shell_stepper(32,device='cuda:0',backend='hvp_graph');m=s.model;cpu=m.reference;bounder=P3ShellBounds(cpu);allrows=[]
for sub in [64,16,4]:
 folder=p/f'trials/sub{sub:03d}';f=json.loads((folder/'failure.json').read_text());raw=folder/'failure_prefix.npz';z=np.load(raw);state=s.state(displacement=z['u_m'][-1],velocity=z['v_m_s'][-1],time_s=z['time_s'][-1]);dt=1/(60*sub);result={'substeps':sub,'input_identity':file_identity(raw),'start_frame':f['frame'],'start_substep':f['substep'],'rows':[],'status':'running'};U=[state.displacement_m];V=[state.velocity_m_s];T=[state.time_s];start=time.perf_counter();lastpulse=start
 for frame in range(f['frame'],f['frame']+3):
  if frame==f['frame']:
   force=m.aerodynamic_force_displacement(z['u_m'][0],z['v_m_s'][0],wind[frame])['force_n'];first=f['substep']
  else:force=m.aerodynamic_force_displacement(state.displacement_m,state.velocity_m_s,wind[frame])['force_n'];first=0
  for i in range(first,sub):
   previous=state
   try:state,diag=s.step(state,force,dt)
   except ShellStepFailed as error:
    result.update(status='numerical_failure',failure_frame=frame,failure_substep=i,reason=error.reason,attempts=error.attempts);break
   # 별도 CPU 물리식으로 저장 u/v에서 가속도를 복구하고 운동방정식을 검산한다.
   e0=cpu.evaluate_displacement(previous.displacement_m);e1=cpu.evaluate_displacement(state.displacement_m);a0=np.zeros_like(force);a0[m.free]=s.mass_factor.solve((force+e0['force_n'])[m.free]);a1=2*(state.velocity_m_s-previous.velocity_m_s)/dt-a0;ma=cpu.mass@a1;residual=ma-e1['force_n']-force;scale=max(np.linalg.norm(x[m.free]) for x in [ma,e1['force_n'],force]);limit=s.policy.force_atol_n+s.policy.force_rtol*scale
   ratio=float(np.linalg.norm(residual[m.free])/limit);update=float(np.max(abs(previous.displacement_m+dt*previous.velocity_m_s+dt*dt/4*(a0+a1)-state.displacement_m)));bounds=bounder.interval(previous.displacement_m,previous.velocity_m_s,state.displacement_m,dt)
   work=float(np.sum(force*(state.displacement_m-previous.displacement_m)));balance=e1['energy_j']+s.kinetic_energy(state.velocity_m_s)-e0['energy_j']-s.kinetic_energy(previous.velocity_m_s)-work
   row={'frame':frame,'substep':i,'force_ratio_cpu':ratio,'update_error_m':update,'geometry_passed':bounds['injectivity_sufficient_condition'],'projected_gradient_upper':bounds['projected_gradient_upper'],'work_error_j':abs(work-diag['external_work_j']),'energy_ledger_error_j':abs(balance-diag['energy_balance_residual_j']),'newton_corrections':diag['newton_corrections']}
   row['verified']=ratio<=1.001 and update<=2e-14 and row['geometry_passed'] and row['work_error_j']<=1e-17+1e-12*abs(work) and row['energy_ledger_error_j']<=3e-16+1e-8*abs(balance)
   result['rows'].append(row);U.append(state.displacement_m);V.append(state.velocity_m_s);T.append(state.time_s)
   if not row['verified']:result.update(status='audit_failure');break
   if time.perf_counter()-lastpulse>20:print(f'분할 {sub}: frame {frame}, substep {i+1}/{sub}, 검산 완료 {len(result["rows"])}',flush=True);lastpulse=time.perf_counter()
  if result['status']!='running':break
 if result['status']=='running':result['status']='passed'
 result['elapsed_s']=time.perf_counter()-start;result['completed_intervals']=len(result['rows']);np.savez_compressed(out/f'sub{sub:03d}.npz',u_m=U,v_m_s=V,time_s=T);result['output_identity']=file_identity(out/f'sub{sub:03d}.npz');(out/f'sub{sub:03d}.json').write_text(json.dumps(result,indent=2)+'\n');allrows.append(result)
 print(json.dumps({k:v for k,v in result.items() if k not in ['rows','attempts']}),flush=True)
summary={'environment':environment,'results':[{'substeps':r['substeps'],'status':r['status'],'completed_intervals':r['completed_intervals'],'max_force_ratio_cpu':max((x['force_ratio_cpu'] for x in r['rows']),default=None),'max_update_error_m':max((x['update_error_m'] for x in r['rows']),default=None)} for r in allrows],'training_eligible':False,'r1_complete':False,'generated_training_samples':0};(out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary),flush=True)
