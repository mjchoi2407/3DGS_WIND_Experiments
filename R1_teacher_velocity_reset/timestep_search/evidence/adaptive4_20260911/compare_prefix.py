"""동일 초기 구간의4배·1배 및 기존 current 경로를 비교한다."""
import json
from pathlib import Path
import numpy as np
from wind3dgs.evaluation.teacher_timestep_trial import compare_trials,read,trial_dir,load_frame
root=Path('experiments/artifacts/runs/teacher_timestep_search');p=root/'20260911_adaptive4_prefix_v1'
result=compare_trials(p,64,256,target_frames=6)
old=root/'20260911_acceleration4_segments_v1';maxdiff={'u_m':0.,'v_m_s':0.,'time_s':0.}
a=read(trial_dir(p,64)/'report.json');b=read(trial_dir(old,64)/'report.json')
for i in range(6):
 x=load_frame(trial_dir(p,64),i,a);y=load_frame(trial_dir(old,64),i,b)
 for key in maxdiff:maxdiff[key]=max(maxdiff[key],float(np.max(abs(x[key]-y[key]))))
r1=read(trial_dir(p,256)/'report.json')
result.update(same_dt_path_max_difference=maxdiff,compute_s_4=a['compute_s'],compute_s_1=r1['compute_s'],compute_speedup=r1['compute_s']/a['compute_s'],costs={str(n):{k:read(trial_dir(p,n)/'report.json')[k] for k in ['setup_s','compute_s','audit_s','write_s']} for n in [64,256]})
(p/'prefix_comparison.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps(result,ensure_ascii=False))
