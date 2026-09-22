"""완료된 첫 공간 실패의 최대 속도 차이를 성분별로 분해한다. 수렴 기준은 바꾸지 않는다."""
from pathlib import Path
import hashlib,json
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.evaluation.teacher_p3_shell_random import QUALITY,file_identity,inspect_run,sources
from wind3dgs.evaluation.teacher_p3_shell_random_comparison import SpatialComparison,map_time
from wind3dgs.evaluation.teacher_p3_shell_random_validation import load_frame
root=Path('experiments/artifacts/runs/teacher_p3_shell_random')
p=root/'verification/scale4_space8_16_s128_v1/natural.json';compare=json.loads(p.read_text())
frame=max(compare['frame_results'],key=lambda r:r['fine_endpoint_peaks']['v_m_s']['error'])['frame']
runs=[root/compare[k] for k in ('first','second')]
configs=[inspect_run(r)[0] for r in runs]
assert all(c['source_sha256']==sources() and c['wind_scale']==4 and c['substeps']==128 for c in configs)
models=[P3Shell(c['resolution'],diagonal=c['diagonal']) for c in configs]
spatial=SpatialComparison(*models)
traces=[load_frame(r,frame)[0] for r in runs]
components=np.zeros((len(traces[0]['v_m_s']),3));reference=np.zeros_like(components)
for A,B,w in spatial.batches:
 a,b=map_time(A,traces[0]['v_m_s']),map_time(B,traces[1]['v_m_s'])
 components+=np.einsum('p,tpc,tpc->tc',w,a-b,a-b)
 reference+=np.einsum('p,tpc,tpc->tc',w,b,b)
index=int(components.sum(axis=1).argmax())
rms=np.sqrt(components[index]/spatial.area_m2)
actual=float(np.sqrt(components[index].sum()/spatial.area_m2))
np.testing.assert_allclose(actual,compare['interpolant_bounds']['v_m_s']['absolute_rms_upper'],rtol=1e-12,atol=1e-15)
report={'frame':frame,'substep':index,'time_s':float(traces[0]['time_s'][index]),
'component_error_rms_m_s':dict(zip(('x','y_initial_normal','z'),map(float,rms))),
'component_squared_error_fraction':dict(zip(('x','y_initial_normal','z'),map(float,components[index]/components[index].sum()))),
'vector_error_rms_m_s':actual,'comparison_sha256':file_identity(p)['sha256'],
'manifest_sha256':{r.name:file_identity(r/'manifest.json')['sha256'] for r in runs},
'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),**QUALITY,
'scope':'최대 차이 시각의 공간 적분 오차 성분 분해. 원인 확정 또는 기준 변경이 아니며 시간/공간 세분과 함께 해석한다.'}
out=root/'verification/scale4_space8_16_peak_components_v1.json'
with out.open('x') as f:json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
