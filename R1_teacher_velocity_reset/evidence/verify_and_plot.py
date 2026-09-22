"""이 실험의 저장 trace 검산과 대표 응답/해상도 진단 그림 재생성."""
import argparse
import json
from pathlib import Path

import numpy as np

from wind3dgs.evaluation.teacher_velocity_reset import verify_run


def rotation_diagnostic(trace, checkpoints):
    """고정된 x=0 모서리를 보존하는 Rz 한 자유도 회전으로 위치 응답을 분해한다."""
    weights = trace['probe_area_weights_m2']
    rest = trace['rest_positions_m'][trace['probe_indices']].astype(float)
    x = trace['probe_positions_m'].astype(float)
    theta = np.arctan2(np.sum(weights[None, :]*rest[None, :, 0]*x[:, :, 1], axis=1),
                       np.sum(weights[None, :]*rest[None, :, 0]*x[:, :, 0], axis=1))
    fit = np.broadcast_to(rest, x.shape).copy()
    fit[:, :, 0] = rest[None, :, 0]*np.cos(theta)[:, None]
    fit[:, :, 1] = rest[None, :, 0]*np.sin(theta)[:, None]
    def rms(delta):
        return np.sqrt(np.sum(delta**2*weights[None, :, None], axis=(1, 2))/weights.sum())
    residual, displacement = rms(x-fit), rms(x-rest)
    return {'method': 'pinned_edge_Rz_area_fit_v1',
            'interpretation': '위치 응답의 회전 성분을 진단한다. 탄성 에너지 비율을 계산한 결과는 아니다.',
            'observations': [{'frame': c, 'time_s': float(trace['time_s'][c]),
                'rotation_deg': float(np.degrees(theta[c])), 'residual_probe_rms_m': float(residual[c]),
                'displacement_probe_rms_m': float(displacement[c]),
                'residual_fraction': float(residual[c]/displacement[c]) if displacement[c] > 1e-12 else None}
                for c in sorted(set(checkpoints) | {len(x)-1})]}


def main():
    parser = argparse.ArgumentParser(description='속도 초기화 실험의 검산 및 대표 그림')
    parser.add_argument('--run', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True, help='새 그림 폴더; 기존 폴더는 덮어쓰지 않음')
    args = parser.parse_args()
    checked = verify_run(args.run)
    report = json.loads((args.run/'report.json').read_text())
    config = json.loads((args.run/'config.json').read_text())['spec']
    n = config['resolutions'][len(config['resolutions'])//2]
    s = config['substeps'][-1]
    branches = ['natural']+[f'reset{c}' for c in config['checkpoints']]
    traces = {}
    for branch in branches:
        with np.load(args.run/f'mesh{n}_sub{s}_{branch}.npz', allow_pickle=False) as data:
            traces[branch] = {k: data[k] for k in data.files}
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    families = {font.name for font in font_manager.fontManager.ttflist}
    for candidate in ('Noto Sans CJK JP', 'Noto Sans CJK KR', 'NanumGothic'):
        if candidate in families:
            plt.rcParams['font.family'] = candidate
            break
    plt.rcParams['axes.unicode_minus'] = False
    args.output.mkdir(parents=True, exist_ok=False)
    natural = traces['natural']
    tip = np.argmin(np.linalg.norm(natural['rest_positions_m']-[1, 0, 0], axis=1))
    fig, axes = plt.subplots(4, 1, figsize=(10, 11), sharex=True, constrained_layout=True)
    for d, axis in enumerate('XYZ'):
        axes[0].plot(natural['time_s'][:-1], natural['wind_velocity_m_s'][:, d], label=axis)
    axes[0].set_ylabel('바람 [m/s]'); axes[0].legend(ncol=3, loc='upper right')
    colors = ['black', 'tab:blue', 'tab:orange', 'tab:green', 'tab:red', 'tab:purple']
    for branch_index, b in enumerate(branches):
        a = traces[b]
        c = 0 if b == 'natural' else int(b[5:])
        t = a['time_s'][c:]
        y = a['positions_m'][c:, tip, 1]*1000
        v = a['velocities_m_s'][c:, tip, 1]*1000
        k = a['kinetic_energy_j'][c:]*1e6
        label = '자연 연속' if b == 'natural' else f'{c/config["fps"]:.1f}s 속도 초기화'
        color = colors[branch_index]
        axes[1].plot(t, y, color=color, label=label)
        if c:
            pre = a['pre_reset_velocity_m_s'][0]
            pre_k = 0.5*np.sum(a['mass_kg'][:, None]*pre.astype(float)**2)*1e6
            v = np.r_[pre[tip, 1]*1000, v]
            k = np.r_[pre_k, k]
            t = np.r_[t[0], t]
        axes[2].plot(t, v, color=color)
        axes[3].plot(t, k, color=color)
    axes[1].set_ylabel('끝점 Y 변위 [mm]'); axes[1].legend(fontsize=9)
    axes[2].set_ylabel('끝점 Y 속도 [mm/s]')
    axes[3].set_ylabel('운동에너지 [μJ]'); axes[3].set_xlabel('절대 시각 [s]')
    for ax in axes:
        ax.grid(alpha=.25)
        for c in config['checkpoints']:
            ax.axvline(c/config['fps'], color='gray', lw=.7, alpha=.35)
    fig.suptitle(f'변화 바람과 위치 보존·속도 초기화 — mesh{n}, substeps{s}\nCPU 개발 탐색 / 학습 적격성 false')
    fig.savefig(args.output/'velocity_reset_response.png', dpi=170)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8), constrained_layout=True)
    for ax, kind, title in zip(axes, ('spatial', 'temporal'), ('공간 비교', '시간 비교')):
        for branch in branches:
            entries = [p for p in report['refinement_pairs'] if p['kind'] == kind and p['branch'] == branch]
            for field, style in (('position', '--'), ('velocity', '-')):
                values = [100*p['metric'][field]['relative_max'] for p in entries]
                label = ('자연' if branch == 'natural' else f'{int(branch[5:])/config["fps"]:.1f}s reset')
                label += ' '+('변위' if field == 'position' else '속도')
                ax.plot(range(len(values)), values, style+'o', label=label)
        labels = ([f'{a}→{b}' for a, b in zip(config['resolutions'], config['resolutions'][1:])]
                  if kind == 'spatial' else [f'{a}→{b}' for a, b in zip(config['substeps'], config['substeps'][1:])])
        ax.set_xticks(range(len(labels)), labels)
        ax.axhline(100*config['diagnostic_relative_limit'], color='red', lw=1, label='개발 진단 1%')
        ax.set_yscale('log'); ax.set_ylabel('상대 최대 probe RMS 차이 [%]')
        ax.set_title(title); ax.set_xlabel('mesh 분할 수' if kind == 'spatial' else 'frame당 substeps')
        ax.grid(alpha=.25); ax.legend(fontsize=7, ncol=2)
    fig.suptitle('공통 frame 표본의 해상도 진단 — 수렴 인증 아님')
    fig.savefig(args.output/'velocity_reset_refinement.png', dpi=170)
    plt.close(fig)
    (args.output/'rotation_diagnostic.json').write_text(
        json.dumps(rotation_diagnostic(natural, config['checkpoints']), ensure_ascii=False, allow_nan=False, indent=2)+'\n',
        encoding='utf-8')
    print(json.dumps(checked, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
