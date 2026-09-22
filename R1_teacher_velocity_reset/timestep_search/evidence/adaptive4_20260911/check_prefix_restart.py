"""완료된 동결0.1초 시험의 복제본을5frame checkpoint로 되돌려 별도GPU worker에서 재개한다."""
import json,shutil,subprocess,sys,os
from pathlib import Path
import numpy as np
from wind3dgs.evaluation.teacher_timestep_search import verify_runtime
from wind3dgs.evaluation.teacher_timestep_trial import read,write,load_frame,trial_dir
root=Path('experiments/artifacts/runs/teacher_timestep_search');source=root/'20260911_adaptive4_prefix_v1';out=root/'20260911_adaptive4_restart_v1';out.mkdir(exist_ok=False)
for name in ['plan.json','wind.npz','runtime_manifest.json','search.json','status.json']:shutil.copy2(source/name,out/name)
shutil.copytree(source/'runtime',out/'runtime');shutil.copytree(trial_dir(source,64),trial_dir(out,64))
r=read(trial_dir(out,64)/'report.json');assert r['completed_frames']==6
r.update(completed_frames=5,frames=r['frames'][:5],status='prefix_passed',compute_s=0.,audit_s=0.,write_s=0.,setup_s=0.,hvp_calls=0)
write(trial_dir(out,64)/'report.json',r)
write(out/'derived_restart.json',{'source':str(source),'restart_after_frame_count':5,'note':'별도 복제본의 보고서만5frame으로 제한. 기존6번째frame 복제 파일은 worker가 recovery로 보존한다. 비용 카운터는 재개 비용만 측정한다.'})
verify_runtime(out)
env=dict(os.environ,PYTHONPATH=str(out/'runtime/code'))
with (out/'worker.log').open('w') as log:subprocess.run([sys.executable,'-u','-m','wind3dgs.evaluation.teacher_timestep_search','--output',str(out),'--frozen','--worker','--substeps','64','--target','6'],env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
frames=[load_frame(trial_dir(p,64),5,read(trial_dir(p,64)/'report.json')) for p in [source,out]]
d={k:float(np.max(abs(frames[0][k]-frames[1][k]))) for k in ['u_m','v_m_s','time_s']}
passed=d['u_m']<=1e-16 and d['v_m_s']<=1e-12 and d['time_s']==0
result={'passed':passed,'max_difference':d,'scope':'n32,4배,0.1초 마지막frame의 별도 프로세스 재개. 전체 긴 궤적 재현성 검증 아님.'}
write(out/'restart_comparison.json',result);print(result)
if not passed:raise RuntimeError('GPU 재개 검증 미달')
