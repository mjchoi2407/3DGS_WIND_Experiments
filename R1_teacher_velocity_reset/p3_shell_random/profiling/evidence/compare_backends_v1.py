"""동일 n32 상태의 기준/HVP 전용/CuPy 시제품 및 원본 I/O·검산 비용 분리."""
import argparse,hashlib,json,time
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_warp import P3ShellWarp,P3ShellWarpStepper
from wind3dgs.teacher.p3_shell_warp_fast import P3ShellWarpFast,P3ShellWarpFastStepper
from wind3dgs.teacher.p3_shell_cupy import P3ShellCuPyStepper
from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy
from wind3dgs.evaluation.teacher_p3_shell_random_validation import load_frame,verify_frame
from wind3dgs.evaluation.teacher_p3_shell_random import file_identity,sources,write_arrays
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
report={'status':'진행 중','results':[],'parent_name':a.parent.name,'manifest':file_identity(a.parent/'manifest.json'),'source_sha256':sources()}
for path in Path('code/wind3dgs/teacher').glob('p3_shell*py'):
 report['source_sha256'][str(path.relative_to('code'))]=hashlib.sha256(path.read_bytes()).hexdigest()
def save(): (a.output/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
save();t=time.perf_counter();trace,metadata=load_frame(a.parent,39);report['load_frame_s']=time.perf_counter()-t
start=236;reference_u=trace['u_m'][start+1];reference_v=trace['v_m_s'][start+1]
for name,Model,Stepper in [('기준',P3ShellWarp,P3ShellWarpStepper),('HVP 전용',P3ShellWarpFast,P3ShellWarpFastStepper),('CuPy 기본 GMRES',P3ShellWarpFast,P3ShellCuPyStepper)]:
 t=time.perf_counter();m=Model(P3Shell(32),device='cuda:0');s=Stepper(m);setup=time.perf_counter()-t
 state=s.state(displacement=trace['u_m'][start],velocity=trace['v_m_s'][start],time_s=float(trace['time_s'][start]));dt=1/(60*256)
 s.step(state,trace['held_force_n'],dt)
 t=time.perf_counter();out,diagnostic=s.step(state,trace['held_force_n'],dt);elapsed=time.perf_counter()-t
 du=float(abs(out.displacement_m-reference_u).max());dv=float(abs(out.velocity_m_s-reference_v).max())
 item=dict(backend=name,setup_s=setup,step_s=elapsed,hvp_calls=diagnostic['hvp_calls'],max_u_difference_m=du,max_v_difference_m_s=dv,force_ratio=diagnostic['force_residual_n']/diagnostic['force_limit_n'],state_close=bool(np.allclose(out.displacement_m,reference_u,rtol=2e-8,atol=2e-12) and np.allclose(out.velocity_m_s,reference_v,rtol=2e-8,atol=2e-10)))
 report['results'].append(item);save();print(item,flush=True)
 del s,m
# I/O and audit costs from unchanged complete frame, not synthetic short-frame timestamps.
t=time.perf_counter();write_arrays(a.output/'frame39_copy.npz',trace);report['compressed_write_s']=time.perf_counter()-t
with np.load(a.output/'frame39_copy.npz',allow_pickle=False) as z:
 report['io_roundtrip_exact']=all(np.array_equal(z[k],v) for k,v in trace.items())
m=P3ShellWarp(P3Shell(32),device='cuda:0');t=time.perf_counter()
report['audit']=verify_frame(m,trace,metadata['steps'],frame=39,substeps=256,policy=ShellSolvePolicy(),cpu_reference=m.reference,wind_scale=4.)
report['full_frame_audit_s']=time.perf_counter()-t;report['status']='완료';save();print('저장·검산 시간',report['compressed_write_s'],report['full_frame_audit_s'],flush=True)
