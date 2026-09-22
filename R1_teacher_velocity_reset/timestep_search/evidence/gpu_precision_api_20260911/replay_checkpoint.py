"""저장 형식 채택 전 고정밀 상태·힘의 별도 진단. 기존 raw와 코드는 수정하지 않는다."""
import json,time,types,sys,inspect,hashlib,zipfile
from pathlib import Path
import numpy as np
from scipy.sparse.linalg import splu
from wind3dgs.teacher import p3_shell as shellmod,p3_shell_kernels as kernels,p3_shell_dynamics as dynamics
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
ld=np.longdouble
if np.finfo(ld).nmant<=np.finfo(float).nmant:raise RuntimeError('확장 가수가 있는 longdouble 환경이 필요합니다')

hp=types.ModuleType('hp_kernels');exec(Path(kernels.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
def arrayld(value,shape,name):
 a=np.array(value,dtype=ld,copy=True)
 if a.shape!=shape or not np.isfinite(a).all():raise ValueError(name)
 return a
force_globals=dict(shellmod.__dict__);force_globals.update(kernels=hp,_array=arrayld)
force_function=types.FunctionType(shellmod.P3Shell.evaluate_displacement.__code__,force_globals);force_function.__kwdefaults__={'direction':None}
class HighPrecisionModel:
 def __init__(self,base):self.base=base;self.reference=base.reference;self.calls=0;self.seconds=0.
 def __getattr__(self,key):return getattr(self.reference,key)
 def evaluate_displacement(self,u,*,direction=None):
  if direction is not None:return self.base.evaluate_displacement(np.asarray(u,dtype=float),direction=np.asarray(direction,dtype=float))
  start=time.perf_counter();r=force_function(self,u);self.calls+=1;self.seconds+=time.perf_counter()-start;return r
class FloatFactor:
 def __init__(self,base):self.base=base
 def solve(self,rhs):return self.base.solve(np.asarray(rhs,dtype=float))
def state128(u,v,t):
 arrays=[np.array(x,dtype=ld,copy=True) for x in (u,v)]
 for x in arrays:x.setflags(write=False)
 return dynamics.ShellState(*arrays,float(t))

from wind3dgs.teacher.p3_shell_warp_precision import P3ShellWarpPrecision,P3ShellWarpPrecisionStepper
from wind3dgs.teacher.p3_shell_precision_state import load_checkpoint
s=P3ShellWarpPrecisionStepper(P3ShellWarpPrecision(shellmod.P3Shell(32),device='cuda:0',capture=True))
p=Path('experiments/artifacts/runs/teacher_timestep_search/20260911_gpu_precision_api_v1');z=np.load(p/'states_hi_lo.npz');U=z['u_hi'].astype(ld)+z['u_lo'].astype(ld);V=z['v_hi'].astype(ld)+z['v_lo'].astype(ld)
state=load_checkpoint(p/'checkpoint.npz',s)
assert np.array_equal(state.displacement_m,U[4]) and np.array_equal(state.velocity_m_s,V[4])
old=np.load(p.parent/'20260911_incremental_newton_v1/sub016.npz');wind=np.load(p.parent/'ten_second_v1/wind.npz')['wind_m_s'];m=s.model;dt=1/(60*16)
force=m.aerodynamic_force_displacement(old['u_m'][-3],old['v_m_s'][-3],wind[160])['force_n'];result,diag=s.step(state,force,dt)
aero_function=types.FunctionType(shellmod.P3Shell.aerodynamic_force_displacement.__code__,force_globals);aero_function.__kwdefaults__=shellmod.P3Shell.aerodynamic_force_displacement.__kwdefaults__
gpu_aero=m.aerodynamic_force_displacement(U[4],V[4],wind[160])
cpu_aero=aero_function(m.reference,U[4],V[4],wind[160])
np.testing.assert_allclose(gpu_aero['force_n'],cpu_aero['force_n'],rtol=2e-12,atol=1e-15)
e0=force_function(m.reference,state.displacement_m);e1=force_function(m.reference,result.displacement_m);a0=np.zeros_like(state.displacement_m);a0[m.free]=s._solve_factor(s.mass_factor,(force+e0['force_n'])[m.free]);a1=2*(result.velocity_m_s-state.velocity_m_s)/dt-a0;ma=m.mass@a1;res=ma-e1['force_n']-force
limit=s.policy.force_atol_n+s.policy.force_rtol*max(np.linalg.norm(x[m.free]) for x in [ma,force,e1['force_n']])
r={'storage_exact':True,'u_max_difference_m':float(np.max(abs(result.displacement_m-U[5]))),'v_max_difference_m_s':float(np.max(abs(result.velocity_m_s-V[5]))),'time_exact':result.time_s==float(z['time_s'][5]),'independent_residual_ratio':float(np.linalg.norm(res[m.free])/limit),'aerodynamic_force_max_difference_n':float(np.max(abs(gpu_aero['force_n']-cpu_aero['force_n'])))}
assert r['u_max_difference_m']<=1e-16 and r['v_max_difference_m_s']<=1e-12 and r['time_exact'] and r['independent_residual_ratio']<=1
print(json.dumps(r),flush=True)
