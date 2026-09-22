"""기존 완결 frame의 읽기·압축 저장·원식 검산 비용 분리."""
import argparse,json,time
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_warp import P3ShellWarp
from wind3dgs.teacher.p3_shell_dynamics import ShellSolvePolicy
from wind3dgs.evaluation.teacher_p3_shell_random import write_arrays,file_identity,sources
from wind3dgs.evaluation.teacher_p3_shell_random_validation import load_frame,verify_frame
p=argparse.ArgumentParser();p.add_argument('--parent',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
r={'status':'진행 중','parent_name':a.parent.name,'source_sha256':sources(),'frame':39,'input_identity':file_identity(a.parent/'frames/039.npz')}
def save(): (a.output/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
t=time.perf_counter();trace,steps=load_frame(a.parent,39);r['read_and_hash_s']=time.perf_counter()-t
print('읽기 완료',r['read_and_hash_s'],flush=True)
t=time.perf_counter();write_arrays(a.output/'frame39_copy.npz',trace);r['compressed_write_s']=time.perf_counter()-t
with np.load(a.output/'frame39_copy.npz',allow_pickle=False) as z:r['roundtrip_exact']=all(np.array_equal(z[k],v) for k,v in trace.items())
save();m=P3ShellWarp(P3Shell(32),device='cuda:0');t=time.perf_counter()
r['audit']=verify_frame(m,trace,steps,frame=39,substeps=256,policy=ShellSolvePolicy(),cpu_reference=m.reference,wind_scale=4.)
r['audit_s']=time.perf_counter()-t;r['status']='완료';save();print('저장·검산 완료',r['compressed_write_s'],r['audit_s'],flush=True)
