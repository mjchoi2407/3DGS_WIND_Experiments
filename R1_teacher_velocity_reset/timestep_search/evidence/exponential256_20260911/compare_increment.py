"""속도 증분 누적형 후보와 이전 수치 참조의 공통 끝 상태 비교."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
b=Path('experiments/artifacts/runs/teacher_timestep_search');m=P3Shell(32)
folders={'increment':'20260911_exponential256_gauss_path20_increment_v1','absolute':'20260911_exponential256_gauss_path20_v1','reference2':'20260911_exponential256_hybrid_ref2_v1','reference4':'20260911_exponential256_hybrid_ref4_v1'}
paths={k:b/v/'endpoint.npz' for k,v in folders.items()};states={}
for name,path in paths.items():
 with np.load(path) as z:states[name]={k:z[k+'_hi'].astype(np.longdouble)+z[k+'_lo'].astype(np.longdouble) for k in ['u','v']}
rows={}
for reference in ['absolute','reference2','reference4']:
 row={'relative_mass_l2':{},'max_absolute_difference':{}}
 for k in ['u','v']:
  d=states['increment'][k]-states[reference][k];y=states[reference][k]
  row['relative_mass_l2'][k]=float(np.sqrt(np.sum(d*(m.mass@d))/np.sum(y*(m.mass@y))))
  row['max_absolute_difference'][k]=float(abs(d).max())
 rows[reference]=row
low_bits={}
for name,path in paths.items():
 with np.load(path) as z:low_bits[name]={'velocity_nonzero_low_components':int(np.count_nonzero(z['v_lo']))}
report={'scope':'증분형 후보 대 이전 절대 속도형 후보/참조의 끝 상태 차이. 전체 시간 곡선·참해 인증 아님.','results':rows,'state_encoding_check':low_bits,'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},'training_eligible':False}
Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(rows),flush=True)
