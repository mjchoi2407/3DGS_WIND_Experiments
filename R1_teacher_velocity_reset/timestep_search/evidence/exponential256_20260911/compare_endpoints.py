"""공통 끝 시각의 질량 L2 차이. 전체 시간 곡선 또는 참해 오차 인증은 아니다."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
base=Path('experiments/artifacts/runs/teacher_timestep_search');m=P3Shell(32)
folders={'one':'20260911_exponential256_gauss_path20_v1','two':'20260911_exponential256_hybrid_ref2_v1','four':'20260911_exponential256_hybrid_ref4_v1'}
paths={k:base/v/'endpoint.npz' for k,v in folders.items() if (base/v/'endpoint.npz').exists()}
paths['gauss6_one']=base/'20260911_gauss256_stage6_followup_v1/endpoint.npz'
paths['legacy_gauss6_ref4']=base/'20260911_gauss256_followup_gaussref4_v1/step3/endpoint.npz'
states={}
for key,path in paths.items():
 with np.load(path) as z:states[key]={k:z[k+'_hi'].astype(np.longdouble)+z[k+'_lo'].astype(np.longdouble) for k in ['u','v']}
results={}
for a,b in [('one','two'),('one','four'),('two','four'),('gauss6_one','four'),('legacy_gauss6_ref4','four')]:
 if a not in states or b not in states:continue
 row={}
 for k in ['u','v']:
  delta=states[a][k]-states[b][k];y=states[b][k]
  row[k]=float(np.sqrt(np.sum(delta*(m.mass@delta))/np.sum(y*(m.mass@y))))
 results[a+'_to_'+b]={'relative_mass_l2':row,'below_one_percent':max(row.values())<.01}
report={'scope':'공통 끝 시각의 수치 차이. 전체 시간 곡선·독립 ODE 참해·누적 오차 인증 아님.','norm':'참조 끝 상태의 질량L2로 정규화','results':results,'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths.values()},'training_eligible':False}
Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(results),flush=True)
