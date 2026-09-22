import json,os,shutil,subprocess,sys,time
from pathlib import Path
import numpy as np
base=Path('experiments/artifacts/runs/teacher_timestep_search');original=base/'20260912_three_scene_validation_v1';root=base/'20260912_three_scene_restart_v1'
root.mkdir(exist_ok=False)
for name in ['plan.json','manifest.json']:shutil.copyfile(original/name,root/name)
for name in ['runtime','inputs']:shutil.copytree(original/name,root/name)
result={}
for shape in ['reference_rectangle','triangular_flag','handkerchief']:
 env=dict(os.environ,PYTHONPATH=str((root/'runtime/code').resolve()),OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1')
 command=[sys.executable,'-u','-m','wind3dgs.evaluation.teacher_three_scene_run',str(root),'--worker',shape]
 with (root/(shape+'.log')).open('w') as log:
  subprocess.run(command+['--stop-after-frames','2'],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240,check=True)
  first=json.loads((root/shape/'report.json').read_text());assert first['status']=='paused' and first['completed_frames']==2
  subprocess.run(command,env=env,stdout=log,stderr=subprocess.STDOUT,timeout=240,check=True)
 second=json.loads((root/shape/'report.json').read_text());assert second['status']=='complete'
 with np.load(original/shape/'frames/002.npz') as a,np.load(root/shape/'frames/002.npz') as b:
  delta={k:float(np.max(abs(a[k].astype(np.longdouble)-b[k].astype(np.longdouble)))) for k in ['u_hi','u_lo','v_hi','v_lo']}
  exact=all(np.array_equal(a[k],b[k]) for k in a.files)
  du=float(np.max(abs((a['u_hi'].astype(np.longdouble)+a['u_lo'])-(b['u_hi'].astype(np.longdouble)+b['u_lo']))))
  dv=float(np.max(abs((a['v_hi'].astype(np.longdouble)+a['v_lo'])-(b['v_hi'].astype(np.longdouble)+b['v_lo']))))
  assert du<=1e-16 and dv<=1e-12
 result[shape]={'first_frames':2,'final_frames':3,'all_trace_arrays_exact':exact,'max_position_difference_m':du,'max_velocity_difference_m_s':dv,'hi_lo_component_differences':delta}
 (root/'restart_checks.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(shape,result[shape],flush=True)
