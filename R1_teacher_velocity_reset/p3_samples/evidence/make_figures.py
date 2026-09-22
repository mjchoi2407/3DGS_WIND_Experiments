"""검증된 P3 원본의 응답과 수렴 요약 그림; 새 simulation은 실행하지 않는다."""
import argparse
import json
from pathlib import Path

import numpy as np

from wind3dgs.teacher.p3_patch_dataset import project_sources, static_arrays


def main():
    parser = argparse.ArgumentParser(description='P3 작은 굽힘 sample의 원본 응답 그림')
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    traces = project_sources(args.source)
    report = json.loads((args.source/'report.json').read_text())
    import matplotlib
    matplotlib.use('Agg')
    from matplotlib import pyplot as plt, font_manager
    fonts = {f.name for f in font_manager.fontManager.ttflist}
    for font in ('Noto Sans CJK JP', 'Noto Sans CJK KR', 'NanumGothic'):
        if font in fonts:
            plt.rcParams['font.family'] = font
            break
    plt.rcParams['axes.unicode_minus'] = False
    args.output.mkdir(parents=True, exist_ok=False)
    tip = np.argmin(np.linalg.norm(static_arrays()['rest_positions_m']-[1, 0, 0], axis=1))
    natural = traces['p3_16_natural']
    fig, axes = plt.subplots(3, 1, figsize=(10, 9), constrained_layout=True, sharex=True)
    for axis, label in enumerate('XYZ'):
        axes[0].plot(natural['time_s'][:-1], natural['wind_velocity_m_s'][:, axis], label=label)
    axes[0].legend(ncol=3); axes[0].set_ylabel('바람 [m/s]')
    for color, (name, trace) in zip(('black', 'tab:blue', 'tab:orange', 'tab:green'), traces.items()):
        start = 0 if name.endswith('natural') else int(name.split('reset')[1])
        label = '자연 연속' if start == 0 else f'{start/60:.1f}s 속도 초기화'
        t = trace['time_s'][start:]
        axes[1].plot(t, trace['probe_positions_m'][start:, tip, 1]*1000, color=color, label=label)
        velocity = trace['probe_velocities_m_s'][start:, tip, 1]*1000
        if start:
            velocity = np.r_[natural['probe_velocities_m_s'][start, tip, 1]*1000, velocity]
            t = np.r_[t[0], t]
        axes[2].plot(t, velocity, color=color)
    axes[1].set_ylabel('끝점 변위 [mm]'); axes[1].legend(fontsize=9)
    axes[2].set_ylabel('끝점 속도 [mm/s]'); axes[2].set_xlabel('시각 [s]')
    for ax in axes:
        ax.grid(alpha=.25)
        for t in (.3, .7, 1.1): ax.axvline(t, color='gray', lw=.6, alpha=.5)
    fig.suptitle('P3 작은 굽힘 — 변화 바람과 위치 보존·속도 초기화\n왼쪽 0.25m 고정 / 전체 모드 / 검증된 범위의 sample 76개')
    fig.savefig(args.output/'p3_response.png', dpi=170); plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5), constrained_layout=True)
    kinds = ['spatial', 'direction', 'quadrature', 'reference_self', 'independent_reference']
    labels = ['P3 8→16', '대각선', '공력 구적', 'spline 16→32', 'P3/spline']
    for ax, metric, title in zip(axes, ('displacement', 'velocity'), ('변위', '속도')):
        values = [100*max(row['metrics'][metric]['continuous_upper_relative'] for row in report['comparisons']
                          if row['kind'] == kind) for kind in kinds]
        ax.bar(np.arange(5), values, color='tab:blue')
        ax.set_xticks(np.arange(5), labels, rotation=20)
        ax.axhline(1., color='red', linestyle='--', label='기준 1%')
        ax.set_ylim(0, 1.12); ax.set_title(title); ax.set_ylabel('연속 시간 오차 상한 [%]')
        ax.grid(axis='y', alpha=.25); ax.legend()
        for i, value in enumerate(values): ax.text(i, value+.025, f'{value:.3f}', ha='center', fontsize=9)
    fig.suptitle('전체 면적 norm / 자연·세 reset 중 최악값 — 모든 비교 통과')
    fig.savefig(args.output/'p3_convergence.png', dpi=170); plt.close(fig)
    print('P3 원본 응답·수렴 그림 생성 완료')


if __name__ == '__main__': main()
