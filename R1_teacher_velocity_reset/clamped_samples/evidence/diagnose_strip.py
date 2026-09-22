"""고정 폭 실험의 정적 굽힘 반례와 저장된 수렴 진단을 재계산한다."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from wind3dgs.evaluation.teacher_bending_audit import evaluate_flat_rest_bending
from wind3dgs.evaluation.teacher_velocity_reset import verify_run
from wind3dgs.teacher.velocity_reset import VelocityResetSpec, make_fixture_mesh


def main():
    parser = argparse.ArgumentParser(description='고정 폭 굽힘 실패 원인 검산; 새 simulation/dataset 없음')
    parser.add_argument('--initial', type=Path, required=True)
    parser.add_argument('--refined', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='새 결과 폴더')
    args = parser.parse_args()
    checked = {label: verify_run(path) for label, path in
               [('initial', args.initial), ('refined', args.refined)]}
    spec = VelocityResetSpec(attachment='left_quarter_strip')
    rows = []
    for n in (4, 8, 16, 32):
        mesh = make_fixture_mesh(spec, n)
        positions = mesh.vertices.astype(float).copy()
        positions[:, 1] += .001 * (np.maximum(positions[:, 0]-.25, 0)/.75)**2
        assert np.array_equal(positions[mesh.pinned], mesh.vertices[mesh.pinned])
        result = evaluate_flat_rest_bending(mesh, positions, edge_ke_n=10.)
        # 각 x strip의 기울기 차이로 계산하는 독립 해석식. Z 길이 합은 1 m다.
        x = np.unique(mesh.vertices[:, 0]).astype(float)
        y = .001 * (np.maximum(x-.25, 0)/.75)**2
        angles = np.arctan(np.diff(y)/np.diff(x))
        analytic = 5. * np.sum(np.diff(angles)**2)
        relative = abs(result['energy_j']-analytic)/analytic
        assert relative < 1e-12
        rows.append({'n': n, **result, 'analytic_energy_j': float(analytic),
                     'analytic_relative_error': float(relative)})
    with np.load(args.initial/'mesh8_sub32_natural.npz', allow_pickle=False) as f:
        rest = f['rest_positions_m'].astype(float)
        xyz = f['probe_positions_m'].astype(float)
        weights = f['probe_area_weights_m2'].astype(float)
        positions = f['positions_m'].astype(float)
        observations = []
        for frame in (18, 42, 66, 90):
            centered = xyz[frame] - np.average(xyz[frame], axis=0, weights=weights)
            covariance = centered.T @ (weights[:, None]*centered)/weights.sum()
            residual = np.sqrt(max(0., np.linalg.eigvalsh(covariance)[0]))
            observations.append({'frame': frame, 'time_s': float(f['time_s'][frame]),
                'max_nodal_displacement_m': float(np.linalg.norm(positions[frame]-rest, axis=1).max()),
                'best_plane_probe_rms_m': float(residual)})
    report = {
        'schema': 'wind3dgs.clamped_strip_failure_diagnosis.v1',
        'status': 'completed', 'physics_resolved': False, 'dataset_issued': False,
        'verification': checked,
        'static': {'attachment': 'x <= 0.25 m', 'free_length_m': .75, 'edge_ke_n': 10.,
            'field': 'delta_Y = 0.001 m * (max(X - 0.25 m, 0) / 0.75 m)^2',
            'energy': '0.5 * edge_ke * sum_internal(rest_edge_length * theta^2)',
            'computation': 'float64 geometry; Newton kernel 실행/전체 shell 에너지 아님',
            'levels': rows, 'energy_ratio_n32_n4': rows[-1]['energy_j']/rows[0]['energy_j']},
        'geometry': {'source': 'initial/mesh8_sub32_natural.npz',
            'measure': '전체 25개 probe의 면적 가중 최적 평면 잔차; 탄성 에너지 비율 아님',
            'observations': observations},
        'interpretation': [
            '현재 BC에서도 고정된 native 계수의 굽힘 에너지가 해상도에 의존한다.',
            '시간 간격과 solver iteration 없이 재현되므로 시간 보완만으로 이 항을 해결할 수 없다.',
            '공간 동역학 오차의 기여율 전부를 이 정적 계산으로 확정하지 않는다.',
            '수렴 기준을 완화하거나 방향 편향으로 탈락한 면적 보정을 재채택하지 않는다.'],
        'sources_sha256': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (
            Path('code/wind3dgs/evaluation/teacher_bending_audit.py'),
            Path('code/wind3dgs/teacher/sample_meshes.py'),
            Path('code/wind3dgs/teacher/velocity_reset.py'))}}
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output/'diagnosis.json').write_text(
        json.dumps(report, ensure_ascii=False, allow_nan=False, indent=2)+'\n', encoding='utf-8')
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt, font_manager
    families = {font.name for font in font_manager.fontManager.ttflist}
    for name in ('Noto Sans CJK JP', 'Noto Sans CJK KR', 'NanumGothic'):
        if name in families:
            plt.rcParams['font.family'] = name
            break
    plt.rcParams['axes.unicode_minus'] = False
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    axes[0].plot([r['n'] for r in rows], [1e6*r['energy_j'] for r in rows], 'o-')
    axes[0].set(xlabel='축당 mesh 구간 수', ylabel='굽힘 에너지 [μJ]',
                title='같은 굽힘 형상인데 에너지가 감소')
    axes[0].set_xticks([4, 8, 16, 32])
    refined = json.loads((args.refined/'report.json').read_text())
    pairs = refined['refinement_pairs']
    indices = np.arange(len(pairs))
    for shift, key, label in [(-.18, 'position', '변위'), (.18, 'velocity', '속도')]:
        axes[1].bar(indices+shift, [100*p['metric'][key]['relative_max'] for p in pairs],
                    width=.36, label=label)
    axes[1].set_xticks(indices, ['자연 연속', '0.3s reset', '0.7s reset', '1.1s reset'])
    axes[1].axhline(1., color='red', linestyle='--', label='개발 진단 1%')
    axes[1].set(ylabel='상대 최대 probe RMS 차이 [%]', title='시간 보완: substeps 64→128')
    axes[1].legend(fontsize=8)
    for ax in axes:
        ax.grid(axis='y', alpha=.25)
    fig.suptitle('왼쪽 0.25m 고정 — 실패 원인 진단 / 물리 수렴 미해결')
    fig.savefig(args.output/'strip_failure_diagnosis.png', dpi=170)
    plt.close(fig)
    print('저장 원본 검산·독립 정적 해석식 대조 완료. 물리 수렴 미해결; dataset 미발행.')


if __name__ == '__main__':
    main()
