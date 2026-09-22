import json,time
from pathlib import Path
from dataclasses import replace
import numpy as np
from wind3dgs.evaluation.teacher_three_scene_run import verify,audit_step,write,runtime_versions
from wind3dgs.evaluation.teacher_timestep_trial import decode_trace
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_samples import load_sample_shell
from wind3dgs.teacher.p3_shell_warp_precision import P3ShellWarpPrecision,P3ShellWarpPrecisionStepper
from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy
from wind3dgs.teacher.p3_shell_adaptive_preconditioner import AdaptivePreconditionerStepper
from wind3dgs.teacher.p3_shell_inexact_newton import InnerSolveTolerance
from wind3dgs.teacher.p3_shell_bounds import P3ShellBounds
base=Path('experiments/artifacts/runs/teacher_timestep_search');old=base/'20260912_three_scenes_10s_v2';plan=verify(old)
out=base/'20260912_three_scene_compat_check_v1';out.mkdir(exist_ok=False);results={}
for shape in ['reference_rectangle','triangular_flag','handkerchief']:
 source=old if shape=='reference_rectangle' else base/'20260912_three_scene_validation_v1'
 frame=363 if shape=='reference_rectangle' else 1
 def trace(index):
  with np.load(source/shape/'frames'/f'{index:03d}.npz') as z:return decode_trace(dict(z),'hi_lo_v1')
 initial=trace(frame-1);expected=trace(frame)
 model=P3Shell(32) if shape=='reference_rectangle' else load_sample_shell(old/'inputs'/f'{shape}.npz')
 raw=P3ShellWarpPrecisionStepper(P3ShellWarpPrecision(model,device='cuda:0',capture=True));official=ShellSolvePolicy(**plan['official_policy'])
 raw.policy=replace(official,force_atol_n=official.force_atol_n*.3,force_rtol=official.force_rtol*.3);raw._linear_tolerance_controller=InnerSolveTolerance(cap=1e-4)
 state=raw.state(displacement=initial['u_m'][-1],velocity=initial['v_m_s'][-1],time_s=float(initial['time_s'][-1]))
 adaptive=AdaptivePreconditionerStepper(raw,switch_iterations=32,rebuild_every=4);bounds=P3ShellBounds(model)
 force=raw.model.aerodynamic_force_displacement(state.displacement_m,state.velocity_m_s,expected['wind_m_s'])['force_n']
 elastic=raw.model.evaluate_displacement(state.displacement_m);du=dv=ratio=0.
 for step in range(64):
  end,d=adaptive.step(state,force,1/(60*64));elastic,check=audit_step(raw,bounds,official,state,end,force,1/(60*64),d,elastic)
  assert not check['flags'],check
  du=max(du,float(np.max(abs(end.displacement_m-expected['u_m'][step+1]))));dv=max(dv,float(np.max(abs(end.velocity_m_s-expected['v_m_s'][step+1]))));ratio=max(ratio,check['force_ratio']);state=end
 assert du<=1e-16 and dv<=1e-12,(du,dv)
 results[shape]={'frame':frame,'steps':64,'position_difference_m':du,'velocity_difference_m_s':dv,'max_force_ratio':ratio,'passed':True}
 write(out/'checks.json',{'runtime_versions':runtime_versions(),'scenes':results});print(shape,results[shape],flush=True)
