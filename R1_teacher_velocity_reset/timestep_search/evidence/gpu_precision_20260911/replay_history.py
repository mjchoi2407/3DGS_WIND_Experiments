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
dynamics._state=state128
s,env=make_shell_stepper(32,device='cuda:0',backend='hvp_graph');original_model=s.model;from wind3dgs.teacher.p3_shell_warp_precision import P3ShellWarpPrecision
from wind3dgs.teacher.p3_shell_warp_fast import _HVPOnlyModel
s.model=_HVPOnlyModel(P3ShellWarpPrecision(original_model.reference,device="cuda:0",capture=True));s.mass_factor=FloatFactor(s.mass_factor)

p=Path('experiments/artifacts/runs/teacher_timestep_search/20260911_gpu_precision_v1');z=np.load(p/'states_hi_lo.npz');U=z['u_hi'].astype(ld)+z['u_lo'].astype(ld);V=z['v_hi'].astype(ld)+z['v_lo'].astype(ld)
base=p.parent/'20260911_incremental_newton_v1';old=np.load(base/'sub016.npz');wind=np.load(p.parent/'ten_second_v1/wind.npz')['wind_m_s'];force=original_model.aerodynamic_force_displacement(old['u_m'][-3],old['v_m_s'][-3],wind[160])['force_n'];dt=1/(60*16);s.preconditioners[dt]=FloatFactor(splu(s.M+(.25*dt*dt)*s.K));state=state128(U[0],V[0],z['time_s'][0])
for i in range(5):
 state,diag=s.step(state,force,dt)
 print(json.dumps({'index':i+1,'u_exact':bool(np.array_equal(state.displacement_m,U[i+1])),'v_exact':bool(np.array_equal(state.velocity_m_s,V[i+1])),'max_u_difference_m':float(np.max(abs(state.displacement_m-U[i+1]))),'max_v_difference_m_s':float(np.max(abs(state.velocity_m_s-V[i+1])))}),flush=True)
