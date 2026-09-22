"""새 삼각 깃발 6프레임 무결성과 대표3단계의 독립 CPU 원식 검산."""
import json
from pathlib import Path
import types

import numpy as np
from scipy.sparse.linalg import splu
from wind3dgs.evaluation.teacher_three_scene_run import digest, read, verify
from wind3dgs.evaluation.teacher_timestep_trial import decode_trace
from wind3dgs.teacher import p3_shell as shell, p3_shell_kernels as kernels
from wind3dgs.teacher.p3_shell_samples import load_sample_shell

root = Path('experiments/artifacts/runs/teacher_timestep_search/20260912_triangle_regular_01s_v1')
plan = verify(root)
folder = root/'triangular_flag'
report = read(folder/'report.json')
assert report['status'] == 'complete' and report['completed_frames'] == len(report['frames']) == 6
steps = []
for i, entry in enumerate(report['frames']):
    assert entry['frame'] == i
    for ext, key in [('npz','trace_sha256'), ('json','metadata_sha256'), ('steps.jsonl','journal_sha256')]:
        assert digest(folder/'frames'/f'{i:03d}.{ext}') == entry[key]
    metadata = read(folder/'frames'/f'{i:03d}.json')
    assert metadata['verified'] and len(metadata['steps']) == 64
    steps.extend(metadata['steps'])
assert len(steps) == 384 and all(not s['flags'] and s['force_ratio'] <= 1 for s in steps)
model = load_sample_shell(root/'inputs/triangular_flag.npz')
mass_solver = splu(model.mass[model.free][:, model.free].tocsc())
hp = types.ModuleType('hp')
exec(Path(kernels.__file__).read_text().replace('dtype=float', 'dtype=np.longdouble'), hp.__dict__)
def array(value, shape, name):
    a = np.array(value, dtype=np.longdouble, copy=True)
    assert a.shape == shape
    return a
namespace = dict(shell.__dict__, kernels=hp, _array=array)
evaluate = types.FunctionType(shell.P3Shell.evaluate_displacement.__code__, namespace)
evaluate.__kwdefaults__ = {'direction': None}
rows = []
dt = 1/(plan['fps']*plan['substeps'])
policy = plan['official_policy']
for frame, step in [(1, 0), (3, 44), (5, 63)]:
    with np.load(folder/'frames'/f'{frame:03d}.npz', allow_pickle=False) as z:
        trace = decode_trace(dict(z), 'hi_lo_v1')
    u0, u1 = trace['u_m'][step:step+2]
    v0, v1 = trace['v_m_s'][step:step+2]
    force = trace['held_force_n']
    e0 = evaluate(model, u0)
    e1 = evaluate(model, u1)
    a0 = np.zeros_like(u0)
    a0[model.free] = mass_solver.solve(np.asarray((force+e0['force_n'])[model.free], dtype=float))
    a1 = 2*(v1-v0)/dt-a0
    ma = model.mass@a1
    limit = policy['force_atol_n']+policy['force_rtol']*max(
        np.linalg.norm(x[model.free]) for x in (ma, force, e1['force_n']))
    ratio = float(np.linalg.norm((ma-force-e1['force_n'])[model.free])/limit)
    update = float(np.max(abs(u0+dt*v0+dt*dt/4*(a0+a1)-u1)))
    pins = bool(np.all(u1[~model.free] == 0) and np.all(v1[~model.free] == 0))
    row = {'frame': frame, 'substep': step, 'end_time_s': float(trace['time_s'][step+1]),
           'cpu_force_ratio': ratio, 'cpu_position_update_error_m': update,
           'cpu_elastic_energy_j': e1['energy_j'], 'pins_exact': pins,
           'passed': ratio <= 1 and update <= 2e-14 and pins}
    rows.append(row)
assert all(row['passed'] for row in rows)
result = {'completed_frames': 6, 'completed_steps': 384, 'duration_s': .1,
          'verified_frame_files': 18, 'all_gpu_step_checks_passed': True,
          'max_gpu_force_ratio': max(s['force_ratio'] for s in steps),
          'internal_target_misses': sum(not s['internal_target_met'] for s in steps),
          'cpu_checks': rows, 'cpu_checks_scope': '대표3단계만 CPU 독립 검산; 전체384단계 CPU 재계산은 아님',
          'plan_sha256': digest(root/'plan.json'), 'manifest_sha256': digest(root/'manifest.json'),
          'report_sha256': digest(folder/'report.json'), 'verifier_sha256': digest(Path(__file__)),
          'ten_seconds_verified': False, 'refinement_verified': False, 'training_eligible': False}
print(json.dumps(result, ensure_ascii=False, indent=2))
