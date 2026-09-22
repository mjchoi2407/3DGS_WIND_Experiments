"""실제 n32 전체 frame과 변형 상태 velocity reset의 opt-in backend 검증."""
import argparse,json,time,hashlib,zipfile
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_warp import P3ShellWarp,P3ShellWarpStepper
from wind3dgs.teacher.p3_shell_warp_fast import P3ShellWarpFast,P3ShellWarpFastStepper
from wind3dgs.teacher.p3_shell_cupy import P3ShellCuPyStepper
from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy
from wind3dgs.evaluation.teacher_p3_shell_random import advance_frame,write_arrays,sources,file_identity
from wind3dgs.evaluation.teacher_p3_shell_random_validation import load_frame,verify_frame
p=argparse.ArgumentParser();p.add_argument('--backend',choices=['fast','cupy'],default='fast');p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
r={'backend':a.backend,'status':'진행 중','frames':[],'source_sha256':sources(),'parent_name':a.parent.name,'parent_manifest':file_identity(a.parent/'manifest.json'),'training_eligible':False,'r1_complete':False,'generated_training_samples':0}
for f in Path('code/wind3dgs/teacher').glob('p3_shell*py'):r['source_sha256'][str(f.relative_to('code'))]=hashlib.sha256(f.read_bytes()).hexdigest()
def save(): (a.output/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
with zipfile.ZipFile(a.output/'source_snapshot.zip','x',compression=zipfile.ZIP_DEFLATED) as z:
 for f in r['source_sha256']:z.write(Path('code')/f,f)
save();base=P3Shell(32);model=P3ShellWarpFast(base,capture=True);stepper=(P3ShellWarpFastStepper if a.backend=='fast' else P3ShellCuPyStepper)(model);reference=P3ShellWarp(base)
for frame in [39,79]:
 trace,_=load_frame(a.parent,frame);state=stepper.state(displacement=trace['u_m'][0],velocity=trace['v_m_s'][0],time_s=float(trace['time_s'][0]))
 print('프레임 전진 시작',frame,flush=True);t=time.perf_counter();state,arrays,diagnostics,error=advance_frame(stepper,state,trace['wind_m_s'],256);wall=time.perf_counter()-t
 if error is not None:raise error
 t=time.perf_counter();write_arrays(a.output/f'frame{frame}.npz',arrays);write_s=time.perf_counter()-t
 np.testing.assert_allclose(arrays['u_m'],trace['u_m'],rtol=2e-8,atol=2e-12)
 np.testing.assert_allclose(arrays['v_m_s'],trace['v_m_s'],rtol=2e-8,atol=2e-10)
 print('프레임 원식 검산 시작',frame,flush=True);t=time.perf_counter()
 audit=verify_frame(reference,arrays,diagnostics,frame=frame,substeps=256,policy=ShellSolvePolicy(),cpu_reference=base,wind_scale=4.)
 entry=dict(frame=frame,simulation_s=wall,compressed_write_s=write_s,audit_s=time.perf_counter()-t,raw_identity=file_identity(a.output/f'frame{frame}.npz'),max_u_difference_m=float(abs(arrays['u_m']-trace['u_m']).max()),max_v_difference_m_s=float(abs(arrays['v_m_s']-trace['v_m_s']).max()),audit=audit)
 r['frames'].append(entry);save();print('프레임 통과',frame,wall,entry['audit_s'],flush=True)
trace,_=load_frame(a.parent,42);cpu=P3ShellWarpStepper(reference)
x=cpu.state(displacement=trace['u_m'][0],velocity=trace['v_m_s'][0],time_s=float(trace['time_s'][0]));y=stepper.state(displacement=trace['u_m'][0],velocity=trace['v_m_s'][0],time_s=float(trace['time_s'][0]));x,ex=cpu.reset_velocity(x);y,ey=stepper.reset_velocity(y)
np.testing.assert_array_equal(y.velocity_m_s,0);np.testing.assert_array_equal(x.displacement_m,y.displacement_m)
force=reference.aerodynamic_force_displacement(x.displacement_m,x.velocity_m_s,trace['wind_m_s'])['force_n']
for _ in range(4):
 x,dx=cpu.step(x,force,1/(60*256));y,dy=stepper.step(y,force,1/(60*256))
 np.testing.assert_allclose(y.displacement_m,x.displacement_m,rtol=2e-8,atol=2e-12)
 np.testing.assert_allclose(y.velocity_m_s,x.velocity_m_s,rtol=2e-8,atol=2e-10)
 assert dy['force_residual_n']<=dy['force_limit_n']
r['reset']=dict(steps=4,removed_kinetic_reference_j=ex,removed_kinetic_gpu_j=ey,max_u_difference_m=float(abs(x.displacement_m-y.displacement_m).max()),max_v_difference_m_s=float(abs(x.velocity_m_s-y.velocity_m_s).max()))
r['status']='완료';save();print('초기화와 전체 검증 완료',flush=True)
