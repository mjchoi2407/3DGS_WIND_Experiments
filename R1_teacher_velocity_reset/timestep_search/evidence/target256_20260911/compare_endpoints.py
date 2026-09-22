"""공통 시작/끝 시각의 국소 끝 상태 차이. 전체 궤적 정확도 판정은 아니다."""
import json,hashlib,sys
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
base=Path('experiments/artifacts/runs/teacher_timestep_search')
sources={1:base/'20260911_target256_current_matrix_v2/restart240_step0.npz',
4:base/'20260911_gmres_restart_probe_v1/restart240_step0.npz',
8:base/'20260911_target256_accuracy_reference_v1/sub8_step7.npz',
16:base/'20260911_target256_accuracy_reference_v1/sub16_step15.npz'}
model=P3Shell(32);states={};times={}
for sub,path in sources.items():
 with np.load(path) as z:
  states[sub]={k:z[k+'_hi'].astype(np.longdouble)+z[k+'_lo'].astype(np.longdouble) for k in ['u','v']}
  times[sub]=float(z['time_s'])
assert max(times.values())-min(times.values())<1e-12
def norm(x):return float(np.sqrt(np.sum(x*(model.mass@x))))
rows=[]
for first,second in [(1,4),(1,8),(1,16),(4,8),(8,16)]:
 row={'first_substeps':first,'second_substeps':second}
 for key in ['u','v']:
  a=states[first][key];b=states[second][key];delta=norm(a-b);scale=norm(b)
  row[key]={'mass_l2_delta':delta,'mass_l2_reference':scale,'relative':delta/max(scale,1e-30)}
 rows.append(row)
report={'time_s':times,'comparisons':rows,'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources.values()},'scope':'공통 입력에서1/60초 후의 국소 공간 L2 끝 상태 비교; 전체 시간 보간/궤적1% 판정은 아님','training_eligible':False}
Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(rows),flush=True)
