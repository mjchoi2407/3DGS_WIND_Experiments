"""새4배 동결 실행기의 n32 실제 GPU 연속/별도 프로세스 재개 비교."""
import os,sys,json,subprocess,time
from pathlib import Path
from argparse import Namespace
import numpy as np
from wind3dgs.evaluation.teacher_timestep_search import prepare,verify_runtime
from wind3dgs.evaluation.teacher_timestep_trial import read,load_frame,trial_dir
root=Path('experiments/artifacts/runs/teacher_timestep_search')
args=Namespace(smoke=False,precision=True,target_substeps=64,linear_cycles=3,linear_restart=240,
 linear_preconditioner='current',preconditioner_rebuild_every=4,pause_after_segment=True,
 segment_seconds=2.5,resolution=32,device='cuda:0',max_trials=None,step_timeout=None,
 trial_timeout=7998,budget_hours=7998/3600)
paths=[root/('20260911_segments4_restart_'+x+'_v1') for x in ['continuous','resumed']]
for p in paths:prepare(p,args)
for index,target in [(0,2),(1,1),(1,2)]:
 p=paths[index];verify_runtime(p);env=dict(os.environ,PYTHONPATH=str(p/'runtime/code'))
 command=[sys.executable,'-u','-m','wind3dgs.evaluation.teacher_timestep_search','--output',str(p),'--frozen','--worker','--substeps','64','--target',str(target)]
 print(f'GPU 재개 검증: {index}, 목표 frame {target}',flush=True)
 with (p/f'worker_{target}.log').open('w') as log:subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=600)
 report=read(trial_dir(p,64)/'report.json')
 if report['completed_frames']!=target:raise RuntimeError(str(report))
frames=[load_frame(trial_dir(p,64),1,read(trial_dir(p,64)/'report.json')) for p in paths]
d={k:float(np.max(abs(frames[0][k]-frames[1][k]))) for k in ['u_m','v_m_s','time_s']}
passed=d['u_m']<=1e-16 and d['v_m_s']<=1e-12 and d['time_s']==0
result={'passed':passed,'max_difference':d,'scope':'n32,4배,rest부터2프레임. 별도 동결 worker 프로세스의 재개 비교. 긴 궤적 검증 아님.'}
(paths[1]/'restart_comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(result,flush=True)
if not passed:raise RuntimeError('재시작 재현성 기준 미달')
