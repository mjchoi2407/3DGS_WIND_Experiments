"""같은 n32 전처리 행렬의 CPU/GPU 풀이를 직접 측정한다."""
import argparse,json,time
from pathlib import Path
import cupy as cp
import numpy as np
from scipy.sparse.linalg import splu
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_dynamics import P3ShellStepper
from wind3dgs.teacher.p3_shell_cupy_linalg import CachedGPULU
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
s=P3ShellStepper(P3Shell(32));A=s.M+(1/(60*256))**2/4*s.K;cpu=splu(A);gpu=CachedGPULU(A)
rhs=np.random.default_rng(123).normal(size=A.shape[0]);d=cp.asarray(rhs);gpu.solve(d);cp.cuda.Stream.null.synchronize()
rows=[]
for _ in range(3):
 t=time.perf_counter();x=cpu.solve(rhs);cpu_s=time.perf_counter()-t
 start=cp.cuda.Event();end=cp.cuda.Event();t=time.perf_counter();start.record();y=gpu.solve(d);end.record();end.synchronize();wall=time.perf_counter()-t
 yy=y.get();res=float(np.linalg.norm(A@yy-rhs)/np.linalg.norm(rhs))
 rows.append(dict(cpu_s=cpu_s,gpu_wall_s=wall,gpu_event_s=cp.cuda.get_elapsed_time(start,end)/1000,relative_residual=res,relative_solution_difference=float(np.linalg.norm(yy-x)/np.linalg.norm(x))))
print(rows,flush=True)
(a.output/'report.json').write_text(json.dumps(dict(status='완료',resolution=32,substeps=256,matrix_shape=A.shape,nnz=A.nnz,plan_reused=True,rows=rows),ensure_ascii=False,indent=2)+'\n')
