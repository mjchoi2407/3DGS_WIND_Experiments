"""구간 중간의 접선 변화 방향 지표. 원인 확정·모드 분해·허용오차 판정은 아니다."""
import json,hashlib
from pathlib import Path
import numpy as np
from wind3dgs.teacher.p3_shell import P3Shell
b=Path('experiments/artifacts/runs/teacher_timestep_search');m=P3Shell(32)
paths={'initial':b/'20260911_gauss256_stage4_v1/endpoint.npz','middle':b/'20260911_exponential256_order4_v1/step0/details.npz','reference':b/'20260911_gauss256_followup_gaussref4_v1/step3/endpoint.npz','gauss6':b/'20260911_gauss256_stage6_followup_v1/endpoint.npz'}
def load(path,key):
 with np.load(path) as z:return z[key+'_hi'].astype(np.longdouble)+z[key+'_lo'].astype(np.longdouble)
u0=load(paths['initial'],'u');um=load(paths['middle'],'midpoint_predictor_u_m')
directions={'frame_displacement':load(paths['reference'],'u')-u0,'initial_velocity':load(paths['initial'],'v'),'gauss6_velocity_difference':load(paths['gauss6'],'v')-load(paths['reference'],'v')}
rows={}
for key,d in directions.items():
 h0=m.evaluate_displacement(u0,direction=d)['hvp_n'];hm=m.evaluate_displacement(um,direction=d)['hvp_n'];mass=np.sum(d*(m.mass@d))
 lam0=float(np.sum(d*h0)/mass);lamm=float(np.sum(d*hm)/mass)
 rows[key]={'relative_hvp_change':float(np.linalg.norm((hm-h0)[m.free])/np.linalg.norm(h0[m.free])),'initial_rayleigh_hz':np.sqrt(lam0)/(2*np.pi) if lam0>=0 else None,'middle_rayleigh_hz':np.sqrt(lamm)/(2*np.pi) if lamm>=0 else None}
p=Path('experiments/R1_teacher_velocity_reset/timestep_search/evidence/exponential256_20260911/tangent_change.json')
p.write_text(json.dumps({'scope':'CPU float64 현재 접선의 방향별 변화 진단. 단일 모드/발생 원인 확정 및 최종 물리 검산 아님.','inputs':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in paths.values()},'rows':rows},ensure_ascii=False,indent=2)+'\n');print(json.dumps(rows),flush=True)
