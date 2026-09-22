"""완료한 두 씬의 저장 움직임·원본 대표 상태 정적 분석. 시간 진행 없음."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from scipy.spatial import cKDTree
from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.teacher.p3_shell_samples import load_sample_shell
from wind3dgs.evaluation.teacher_three_scene_run import digest, verify

shape = sys.argv[1]
assert shape in ('reference_rectangle','handkerchief')
root = Path('experiments/artifacts/runs/teacher_timestep_search/20260912_three_scenes_10s_v4')
cache = Path('experiments/artifacts/runs/shell_playback/20260913_completed_v1')/shape
plan = verify(root)
report_path = root/shape/'report.json'
report = json.loads(report_path.read_text())
identity = json.loads((cache/'manifest.json').read_text())
assert digest(report_path) == identity['source_report_sha256']
assert all(digest(cache/k) == v for k,v in identity['files'].items())
assert report['status'] == 'complete' and report['completed_frames'] == 600
model = P3Shell(32) if shape == 'reference_rectangle' else load_sample_shell(root/'inputs'/f'{shape}.npz')
X = model.rest_positions
weights = np.asarray(model.mass.sum(axis=1)).ravel()
assert np.all(weights > 0)
weights /= weights.sum()
center0 = weights@X
A = X-center0

def geometry(x):
    center = weights@x
    B = x-center
    cov = B.T@(weights[:,None]*B)
    eigenvalues,eigenvectors = np.linalg.eigh(cov)
    normal = eigenvectors[:,0]
    left,_,right = np.linalg.svd(A.T@(weights[:,None]*B))
    correction = np.eye(3); correction[-1,-1] = np.linalg.det(left@right)
    rotation = left@correction@right
    residual = B-A@rotation
    disp = x-X
    rms = np.sqrt(np.sum(weights[:,None]*disp**2))
    rigid = np.sqrt(np.sum(weights[:,None]*residual**2))
    return {'rms_displacement_m':float(rms), 'max_displacement_m':float(np.linalg.norm(disp,axis=1).max()),
            'best_rigid_residual_rms_m':float(rigid), 'best_plane_rms_m':float(np.sqrt(max(0,eigenvalues[0]))),
            'plane_tilt_deg':float(np.degrees(np.arccos(np.clip(abs(normal@model.rest_normal),0,1)))),
            'centroid_y_displacement_m':float(center[1]-center0[1]),
            'rigid_residual_fraction_squared':float(rigid**2/rms**2) if rms>1e-8 else None}

positions = np.load(cache/'positions.npy',mmap_mode='r')
rows = [dict(time_s=i/60,**geometry(np.asarray(x,dtype=float))) for i,x in enumerate(positions)]
peak = int(np.argmax([r['rms_displacement_m'] for r in rows]))
plane_peak = int(np.argmax([r['best_plane_rms_m'] for r in rows]))
selected = sorted(set([60*i for i in range(1,11)]+[peak,plane_peak]))
V = model.volume
rest_q = np.einsum('eqi,eic->eqc',V.N,X[V.ids])
radius = .1*np.linalg.norm(np.ptp(X,axis=0))
dist = cKDTree(X[~model.free]).query(rest_q.reshape(-1,3))[0].reshape(V.weights.shape)
near = dist <= radius
near_area = float(V.weights[near].sum()/V.weights.sum())

def weighted_quantile(a,w,q):
    a,w = np.asarray(a,dtype=float),np.asarray(w,dtype=float)
    order = np.argsort(a)
    return float(np.interp(q*np.sum(w),np.cumsum(w[order]),a[order]))

details = []
for index in selected:
    frame = index-1
    path = root/shape/'frames'/f'{frame:03d}.npz'
    assert digest(path) == report['frames'][frame]['trace_sha256']
    with np.load(path,allow_pickle=False) as z:
        hi,lo = z['u_hi'],z['u_lo']
        u = hi[-1].astype(np.longdouble)+lo[-1].astype(np.longdouble)
        full_u = hi+lo
        alpha = np.linspace(0,1,len(full_u))[:,None,None]
        linear_path = full_u[0]+alpha*(full_u[-1]-full_u[0])
        subframe_departure = float(np.linalg.norm(full_u-linear_path,axis=2).max())
        velocity = z['v_hi'][-1].astype(np.longdouble)+z['v_lo'][-1].astype(np.longdouble)
        wind = z['wind_m_s'].copy()
    x = X+u.astype(float)
    assert np.max(abs(x-positions[index])) < 1e-7
    e = model.evaluate_displacement(u)
    F,H = V.geometry(u); F += model.rest_tangents
    normal = np.cross(F[:,:,0],F[:,:,1]); normal /= np.linalg.norm(normal,axis=-1)[...,None]
    average = np.sum(V.weights[...,None]*normal,axis=(0,1)); average /= np.linalg.norm(average)
    angles = np.degrees(np.arccos(np.clip(normal@average,-1,1)))
    curvature = np.sum(H*normal[...,None,:],axis=-1)
    bending_density = .5*np.einsum('eqa,ab,eqb->eq',curvature,model.db,curvature)
    bending_q = V.weights*bending_density
    bending = float(bending_q.sum())
    penalty_parts = {'interior':0.,'boundary':0.}
    for batches,mu,penalty,boundary in model.edge_groups:
        ns=[]
        for b in batches:
            f,_=b.geometry(u);f+=model.rest_tangents
            n=np.cross(f[:,:,0],f[:,:,1]);n/=np.linalg.norm(n,axis=-1)[...,None];ns.append(n)
        jump=ns[0]-(model.rest_normal if boundary else ns[1])
        penalty_parts['boundary' if boundary else 'interior'] += float(np.sum(batches[0].weights*penalty*.5*np.sum(jump**2,axis=-1)))
    detail = dict(time_s=index/60, trace_sha256=digest(path),**geometry(x),
                  **{k:e[k] for k in ('energy_j','membrane_energy_j','bending_volume_energy_j','edge_energy_j',
                                     'max_strain_component','min_area_ratio','max_normal_jump','max_boundary_normal_jump')})
    detail.update(kinetic_energy_j=float(.5*np.sum(velocity*(model.mass@velocity))),wind_m_s=wind.tolist(),
                  subframe_departure_from_linear_endpoints_max_m=subframe_departure,
                  normal_spread_p95_deg=weighted_quantile(angles.ravel(),V.weights.ravel(),.95),
                  bending_energy_near_fixed_fraction=float(bending_q[near].sum()/bending) if bending>0 else None,
                  penalty_energy_j=penalty_parts,
                  edge_consistency_energy_j=e['edge_energy_j']-sum(penalty_parts.values()))
    details.append(detail)
    print(f'{shape}: 원본 {index/60:.3f}초 정적 분석 완료',file=sys.stderr,flush=True)
active=[r for r in rows if r['max_displacement_m']>=.05]
with np.load(root/'inputs/wind.npz') as z:w=z['wind_m_s']
result={'shape':shape,'scope':'전체601시각은 hash검증 표시캐시의 형상 통계; 대표 시각은 원본 hi/lo 정적 재평가. 시간 진행·물리 수렴 판정 없음',
        'source_report_sha256':digest(report_path),'source_manifest_sha256':digest(root/'manifest.json'),
        'analysis_script_sha256':digest(Path(__file__)),'display_cache_rounding_error_m':identity['max_display_rounding_error_m'],
        'material_scales':dict(zip(['membrane_n_per_m','bending_n_m'],model.material.scales())),
        'fixed_p3_nodes':int((~model.free).sum()),'p3_nodes':len(X),'near_fixed_radius_m':float(radius),
        'near_fixed_rest_area_fraction':near_area,'peak_displacement_time_s':peak/60,
        'peak_plane_residual_time_s':plane_peak/60,'active_definition':'최대 변위 5cm 이상',
        'active_frame_count':len(active),
        'active_rigid_residual_fraction_squared_median':float(np.median([r['rigid_residual_fraction_squared'] for r in active])),
        'active_rigid_residual_fraction_squared_max':float(max(r['rigid_residual_fraction_squared'] for r in active)),
        'wind_speed_max_m_s':float(np.linalg.norm(w,axis=1).max()),'wind_speed_rms_m_s':float(np.sqrt(np.mean(np.sum(w*w,axis=1)))),
        'trajectory_geometry':rows,'original_state_details':details}
print(json.dumps(result,ensure_ascii=False,indent=2))
