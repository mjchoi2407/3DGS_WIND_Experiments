import numpy as np,types,json
from pathlib import Path
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher import p3_shell_kernels as k
m=P3Shell(32);ld=np.longdouble
hp=types.ModuleType('hp');exec(Path(k.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
z=dict(np.load('/tmp/wind3dgs_newton_state.npz'))
def force(u,mode):
 use64=mode=='geometry64';K=k if mode=='kernel64' else hp
 V=m.volume;F,H=V.geometry(u.astype(float) if use64 else u.astype(ld));F=F.astype(ld)+m.rest_tangents.astype(ld)
 if use64:F=(F.astype(float)).astype(ld)
 r=K.volume(F,H,m.dm,m.db);parts=[];g=np.zeros(u.shape,dtype=ld);np.add.at(g,V.ids,V.adjoint(r['gradient_F'],r['gradient_H']));parts.append(-g.copy())
 for batches,mu,penalty,boundary in m.edge_groups:
  geometries=[b.geometry(u.astype(float) if use64 else u.astype(ld)) for b in batches]
  geometries=[(F.astype(ld)+m.rest_tangents.astype(ld),H) for F,H in geometries]
  if use64:geometries=[(F.astype(float).astype(ld),H) for F,H in geometries]
  r=K.edge([F for F,H in geometries],[H for F,H in geometries],mu,penalty,m.db,fixed_normal=m.rest_normal if boundary else None)
  part=np.zeros(u.shape,dtype=ld)
  for i,b in enumerate(batches):np.add.at(part,b.ids,b.adjoint(*r['gradients'][i]))
  parts.append(-part.copy());g+=part
 return -g,parts
norm=lambda x:float(np.linalg.norm(x[m.free]))
u=z['best_u'];base,parts=force(u,'all128');inertia=(m.mass.astype(ld)@z['best_a'].astype(ld));out={'longdouble_bits':int(np.finfo(ld).nmant),'stored_residual':float(z['best_norm']),'force_limit':float(z['force_limit']),'highprecision_residual':norm(inertia-base-z['force']), 'gpu_vs_highprecision_force':norm(z['best_force']-base)}
for mode in ['geometry64','kernel64']:
 f,p=force(u,mode);out[mode]={'force_error':norm(f-base),'parts_error':[norm(a-b) for a,b in zip(p,parts)]}
du=z['c'].astype(ld)*z['delta'].astype(ld)
uplus=(z['u0']+(z['dt']*z['v0']+z['c']*(z['a0']+(z['a']+z['delta']))))
actual=uplus-u;out['update']={'desired_norm':norm(du),'actual_norm':norm(actual),'relative_representation_error':norm(actual-du)/norm(du),'unchanged_components':int(np.sum(actual[m.free]==0)),'free_components':int(actual[m.free].size)}
H=m.evaluate_displacement(u,direction=np.asarray(du,dtype=float))['hvp_n'];f_plus,_=force(u.astype(ld)+du,'all128');out['actual_direction_highprecision_derivative_relative_error']=norm((base-f_plus)-H)/norm(H)
# 같은 가속도의 확장 정밀도 위치를 비교하며 입력 상태는 바꾸지 않는다.
uideal=z['u0'].astype(ld)+z['dt'].astype(ld)*z['v0'].astype(ld)+z['c'].astype(ld)*(z['a0'].astype(ld)+z['best_a'].astype(ld))
fideal,_=force(uideal,'all128');out['ideal_state_residual']=norm(inertia-fideal-z['force']);out['state_rounding_force_difference']=norm(base-fideal)
print(json.dumps(out,indent=2),flush=True);Path('/tmp/wind3dgs_precision_split.json').write_text(json.dumps(out,indent=2)+'\n')
