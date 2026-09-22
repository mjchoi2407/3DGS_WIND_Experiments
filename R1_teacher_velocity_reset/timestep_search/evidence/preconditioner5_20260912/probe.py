"""동일159~163번 연속5frame의 보조 풀이 비용 비교. 본 실행은 미변경."""
import json,time,zipfile,shutil
from pathlib import Path
from dataclasses import replace
import numpy as np
from wind3dgs.evaluation.teacher_three_scene_run import verify,write,digest,audit_step,runtime_versions
from wind3dgs.evaluation.teacher_timestep_trial import decode_trace,encode_trace
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_warp_precision import P3ShellWarpPrecision,P3ShellWarpPrecisionStepper
from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy,ShellStepFailed
from wind3dgs.teacher.p3_shell_adaptive_preconditioner import AdaptivePreconditionerStepper
from wind3dgs.teacher.p3_shell_inexact_newton import InnerSolveTolerance
from wind3dgs.teacher.p3_shell_bounds import P3ShellBounds
base=Path('experiments/artifacts/runs/teacher_timestep_search');source=base/'20260912_three_scenes_10s_v2';out=base/'20260912_preconditioner5_v1';out.mkdir(exist_ok=False)
plan=verify(source);folder=source/'reference_rectangle';original=json.loads((folder/'report.json').read_text());identities={}
def trace(frame):
 p=folder/'frames'/f'{frame:03d}.npz';entry=original['frames'][frame]
 assert digest(p)==entry['trace_sha256'];identities[str(p)]=entry['trace_sha256']
 with np.load(p) as z:return decode_trace(dict(z),'hi_lo_v1')
initial=trace(158);targets={i:trace(i) for i in range(159,164)};baseline=[]
for frame in targets:
 p=folder/'frames'/f'{frame:03d}.json';assert digest(p)==original['frames'][frame]['metadata_sha256'];identities[str(p)]=digest(p);baseline.append(json.loads(p.read_text()))
with zipfile.ZipFile(out/'source.zip','w',zipfile.ZIP_DEFLATED) as z:
 for p in Path('code/wind3dgs').rglob('*.py'):z.write(p,str(p))
shutil.copyfile(__file__,out/'probe.py');write(out/'input_identity.json',identities)
model=P3Shell(32);raw=P3ShellWarpPrecisionStepper(P3ShellWarpPrecision(model,device='cuda:0',capture=True));official=ShellSolvePolicy(**plan['official_policy']);raw.policy=replace(official,force_atol_n=official.force_atol_n*.3,force_rtol=official.force_rtol*.3)
bounder=P3ShellBounds(model);report={'runtime_versions':runtime_versions(),'frames':[159,160,161,162,163],'baseline_source':str(source),'baseline_solve_s':sum(x['solve_s'] for x in baseline),'baseline_hvp':sum(x['hvp_calls'] for f in baseline for x in f['steps']),'historical_timing_comparison':True,'trials':[]}
def save():write(out/'report.json',report)
for name,threshold,reuse in [('rest_until_failure',10**9,4),('reuse16',32,16),('reuse64',32,64)]:
 raw._linear_tolerance_controller=InnerSolveTolerance(cap=1e-4);state=raw.state(displacement=initial['u_m'][-1],velocity=initial['v_m_s'][-1],time_s=float(initial['time_s'][-1]));rows=[];trial={'name':name,'threshold':threshold,'rebuild_every':reuse,'status':'running','rows':rows,'solve_s':0.,'audit_s':0.,'max_u_difference_m':0.,'max_v_difference_m_s':0.};report['trials'].append(trial);(out/name).mkdir();save()
 for frame in range(159,164):
  raw.preconditioners.clear();s=AdaptivePreconditionerStepper(raw,switch_iterations=threshold,rebuild_every=reuse);target=targets[frame]
  force=raw.model.aerodynamic_force_displacement(state.displacement_m,state.velocity_m_s,target['wind_m_s'])['force_n'];elastic=raw.model.evaluate_displacement(state.displacement_m);U=[state.displacement_m];V=[state.velocity_m_s];T=[state.time_s]
  failed=False
  for step in range(64):
   start=time.perf_counter()
   try:end,d=s.step(state,force,1/(60*64))
   except (ShellStepFailed,ValueError) as error:
    trial.update(status='numerical_failure',frame=frame,substep=step,reason=str(error),attempts=getattr(error,'attempts',[]),failed_s=time.perf_counter()-start);failed=True;break
   elapsed=time.perf_counter()-start;trial['solve_s']+=elapsed;start=time.perf_counter()
   elastic,check=audit_step(raw,bounder,official,state,end,force,1/(60*64),d,elastic);trial['audit_s']+=time.perf_counter()-start
   trial['max_u_difference_m']=max(trial['max_u_difference_m'],float(np.max(abs(end.displacement_m-target['u_m'][step+1]))));trial['max_v_difference_m_s']=max(trial['max_v_difference_m_s'],float(np.max(abs(end.velocity_m_s-target['v_m_s'][step+1]))))
   rows.append({'frame':frame,'substep':step,'solve_s':elapsed,'attempts':d['attempts'],'hvp_calls':d['hvp_calls'],'newton_corrections':d['newton_corrections'],'adaptive':d['adaptive_preconditioner'],**check})
   if check['flags']:trial.update(status='audit_failure',frame=frame,substep=step);failed=True;break
   state=end;U.append(state.displacement_m);V.append(state.velocity_m_s);T.append(state.time_s)
  with (out/name/f'{frame:03d}.npz').open('xb') as f:np.savez_compressed(f,**encode_trace({'u_m':np.asarray(U),'v_m_s':np.asarray(V),'time_s':np.asarray(T)},'hi_lo_v1'))
  save();print(name,frame,len(rows),round(trial['solve_s'],2),trial['status'],flush=True)
  if failed:break
 if len(rows)==320 and all(not x['flags'] for x in rows):trial['status']='passed'
 save()
