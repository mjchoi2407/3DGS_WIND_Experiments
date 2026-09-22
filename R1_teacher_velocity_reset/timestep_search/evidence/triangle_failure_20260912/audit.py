"""동결 입력의 정적 에너지·메시 검사. 시간 진행이나 원본 변경 없음."""
import json
from pathlib import Path

import numpy as np
from scipy.linalg import cholesky
from scipy.sparse.linalg import eigsh

from wind3dgs.evaluation.teacher_three_scene_run import digest, verify
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_samples import load_sample_shell
from wind3dgs.teacher.sample_meshes import make_triangular_flag

root = Path('experiments/artifacts/runs/teacher_timestep_search/20260912_three_scenes_10s_v4')
verify(root)
folder = root / 'triangular_flag'
model = load_sample_shell(root / 'inputs/triangular_flag.npz')
with np.load(folder / 'last_valid_state.npz') as z:
    u = z['u_hi'] + z['u_lo']
    v = z['v_hi'] + z['v_lo']
    state_time = float(z['time_s'])

def quality(vertices, faces):
    p = vertices[faces].astype(float)
    area = np.linalg.norm(np.cross(p[:, 1]-p[:, 0], p[:, 2]-p[:, 0]), axis=1)/2
    lengths2 = sum(np.sum((p[:, (i+1)%3]-p[:, i])**2, axis=1) for i in range(3))
    return {'faces': len(faces), 'quality_min_median_max': np.quantile(4*np.sqrt(3)*area/lengths2, [0, .5, 1]).tolist()}

with np.load(root / 'inputs/triangular_flag.npz') as z:
    old_quality = quality(z['vertices'], z['faces'])
K = model.rest_stiffness()
ids = 3*np.flatnonzero(model.free)+1
bending = K[ids][:, ids]
values, vectors = eigsh(bending, k=1, which='SA', tol=1e-6, maxiter=1500,
                       v0=np.random.default_rng(0).normal(size=len(ids)))
q = vectors[:, 0]
energies = []
for scale in (1., .01):
    r = model.evaluate_displacement(scale*u)
    energies.append({'displacement_scale': scale, **{k: r[k] for k in (
        'energy_j', 'membrane_energy_j', 'bending_volume_energy_j', 'edge_energy_j',
        'max_strain_component', 'min_area_ratio')}})
mesh = make_triangular_flag(width_m=1.2, height_m=.75, resolution=(24, 16))
candidate = P3Shell(sample_mesh=mesh)
ids2 = 3*np.flatnonzero(candidate.free)+1
A = candidate.rest_stiffness()[ids2][:, ids2].toarray()
L = cholesky(A, lower=True)
result = {
    'scope': 'CPU 정적 진단. 후보 메시를 메모리에만 생성. GPU·시간 진행·수렴 검증 미실행',
    'source_hashes': {str(p): digest(p) for p in (root/'manifest.json', root/'inputs/triangular_flag.npz', folder/'failure.json', folder/'last_valid_state.npz')},
    'diagnostic_script_sha256': digest(Path(__file__)),
    'state_time_s': state_time, 'old_mesh': old_quality,
    'max_displacement_m': float(np.linalg.norm(u, axis=1).max()),
    'max_velocity_m_s': float(np.linalg.norm(v, axis=1).max()),
    'kinetic_energy_j': float(.5*np.sum(v*(model.mass@v))),
    'linear_energy_j': float(.5*u.ravel()@(K@u.ravel())), 'nonlinear_energy': energies,
    'old_rest_bending_eigenvalue': float(values[0]),
    'eigenpair_relative_residual': float(np.linalg.norm(bending@q-values[0]*q)/max(1, abs(values[0]))),
    'candidate_mesh': quality(mesh.vertices, mesh.faces),
    'candidate_rest_bending_cholesky': 'passed',
    'candidate_cholesky_relative_reconstruction': float(np.linalg.norm(L@L.T-A)/np.linalg.norm(A)),
    'candidate_adopted': False,
}
print(json.dumps(result, ensure_ascii=False, indent=2))
