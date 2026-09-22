import types
from pathlib import Path
import numpy as np
from wind3dgs.teacher import p3_shell as sm,p3_shell_kernels as k
from wind3dgs.teacher.p3_shell_execution import make_shell_stepper
from wind3dgs.teacher.p3_shell_warp_precision import P3ShellWarpPrecision
hp=types.ModuleType('hp');exec(Path(k.__file__).read_text().replace('dtype=float','dtype=np.longdouble'),hp.__dict__)
def arr(v,shape,name):
 a=np.asarray(v,dtype=np.longdouble);assert a.shape==shape;return a
fg=dict(sm.__dict__);fg.update(kernels=hp,_array=arr)
f=types.FunctionType(sm.P3Shell.evaluate_displacement.__code__,fg);f.__kwdefaults__={'direction':None}
s,env=make_shell_stepper(32,device='cuda:0',backend='hvp_graph');m=P3ShellWarpPrecision(s.model.reference,device='cuda:0',capture=True)
z=np.load('experiments/artifacts/runs/teacher_timestep_search/20260911_highprecision_state_v2/states_hi_lo.npz')
for i in (0,1,8):
 u=z['u_hi'][i].astype(np.longdouble)+z['u_lo'][i].astype(np.longdouble)
 ref=f(m.reference,u)['force_n'];r=m.evaluate_displacement(u)['force_n'];old=s.model.evaluate_displacement(u)['force_n']
 print(i,'precision_error',float(np.linalg.norm((r-ref)[m.free])),'old_error',float(np.linalg.norm((old-ref)[m.free])),flush=True)
