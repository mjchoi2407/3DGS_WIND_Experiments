"""속도 차이의 현재 접선 Rayleigh quotient 진단. 모드 분해/필터 채택은 아니다."""
import json,sys,hashlib
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.evaluation.teacher_timestep_trial import decode_trace
base=Path('experiments/artifacts/runs/teacher_timestep_search')
s,_=make_shell_stepper(32,device='cuda:0',backend='precision_hvp_graph');m=s.model
source=base/'20260911_precision_segments_v3/trials/sub004/failure_prefix.npz'
with np.load(source) as z:u0=decode_trace(dict(z),'hi_lo_v1')['u_m'][0]
ref=base/'20260911_target256_accuracy_refine_v1/sub32_step31.npz'
def velocity(path):
 with np.load(path) as z:return z['v_hi'].astype(np.longdouble)+z['v_lo'].astype(np.longdouble)
vref=velocity(ref)
paths={'newmark':base/'20260911_target256_current_matrix_v2/restart240_step0.npz',
'gauss2':base/'20260911_gauss256_v1/endpoint.npz','gauss3':base/'20260911_gauss256_stage3_v1/endpoint.npz'}
rows={}
for name,path in paths.items():
 d=velocity(path)-vref;hd=m.evaluate_displacement(u0,direction=d)['hvp_n'];md=m.mass@d
 mass=float(np.sum(d*md));stiffness=float(np.sum(d*hd));omega2=stiffness/mass
 rows[name]={'relative_velocity_mass_l2':float(np.sqrt(mass/np.sum(vref*(m.mass@vref)))),
             'rayleigh_frequency_hz':float(np.sqrt(omega2)/(2*np.pi)) if omega2>=0 else None,
             'stiffness_quadratic':stiffness,'mass_quadratic':mass,'omega_dt':float(np.sqrt(omega2)/60) if omega2>=0 else None,
             'endpoint_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
report={'rows':rows,'input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'reference_sha256':hashlib.sha256(ref.read_bytes()).hexdigest(),
'scope':'초기 현재 접선에 대한 오차 방향 Rayleigh quotient. 여러 모드가 섞인 가중 지표이며 단일 진동수/모드 분포를 뜻하지 않는다. 물리 항/속도 필터를 적용하지 않음'}
Path(sys.argv[1]).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(rows),flush=True)
