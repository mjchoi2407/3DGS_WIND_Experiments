"""검산된 natural과 세 reset suffix의 실제 수치 시계열을 그리는 실험 wrapper."""
import argparse
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

from wind3dgs.teacher.p3_shell import P3Shell
from wind3dgs.evaluation.teacher_p3_shell_random import QUALITY, file_identity, inspect_run, wind_program
from wind3dgs.evaluation.teacher_p3_shell_random_validation import load_frame
from wind3dgs.evaluation.teacher_p3_shell_random_comparison import area_rms, map_time


def series(run, verification):
    config, report = inspect_run(run)
    audit = json.loads(verification.read_text())
    if not audit['verified'] or audit['run'] != run.name or audit['manifest_sha256'] != file_identity(run/'manifest.json')['sha256']:
        raise ValueError('원본과 연결된 완료 검산이 필요합니다')
    model = P3Shell(config['resolution'], diagonal=config['diagonal'])
    tip = model.moving_surface_map(np.array([[1., .5]]))
    output = {key: [] for key in ('time_s', 'tip_y_m', 'velocity_rms_m_s', 'kinetic_j')}
    for frame in range(config['start_frame'], config['end_frame']):
        trace, _ = load_frame(run, frame)
        pick = slice(None) if frame == config['start_frame'] else slice(1, None)
        rms = area_rms(model, trace['v_m_s'])
        kinetic = .5*model.density*(float(model.mass.sum())/model.density)*rms*rms
        values = {'time_s': trace['time_s'], 'tip_y_m': map_time(tip, trace['u_m'])[:, 0, 1],
                  'velocity_rms_m_s': rms, 'kinetic_j': kinetic}
        for key, value in values.items():
            output[key].append(value[pick])
    return {k: np.concatenate(v) for k, v in output.items()}, report, audit, config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('natural', type=Path)
    parser.add_argument('--verification', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('기존 그림을 덮어쓸 수 없습니다')
    plt.rcParams.update({'font.family': 'Noto Sans CJK KR', 'axes.unicode_minus': False, 'font.size': 9, 'pdf.fonttype': 42})
    fig, axes = plt.subplots(2, 2, figsize=(11, 7), layout='constrained')
    natural_config, _ = inspect_run(args.natural)
    wind, _ = wind_program(natural_config['wind_scale'])
    time = np.arange(91)/60
    for i, label in enumerate(('x', 'y (초기 법선)', 'z')):
        axes[0, 0].step(time, np.r_[wind[:, i], wind[-1, i]], where='post', label=label, lw=1.2)
    axes[0, 0].set(title='입력 바람 (60 Hz)', ylabel='풍속 성분 (m/s)')
    axes[0, 0].axvspan(1.2, 1.5, color='.93', zorder=-1)
    provenance = {'series': {}, 'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(), **QUALITY,
                  'velocity_rms_reference_area_m2': .75,
                  'scope': '검산 원본의 실제 substep 시계열. Reset 분기는 공통 prefix 이후만 표시하며 공간·시간 수렴 판정은 별도'}
    for name, suffix, label, color in (('natural', '', '자연 응답', '#0072B2'),
            ('reset18', '_reset18', '0.3 s 속도 0', '#D55E00'),
            ('reset42', '_reset42', '0.7 s 속도 0', '#009E73'),
            ('reset66', '_reset66', '1.1 s 속도 0', '#CC79A7')):
        run = args.natural.with_name(args.natural.name+suffix)
        verification = args.verification/(name+'.json')
        values, report, audit, config = series(run, verification)
        t = values['time_s']
        axes[0, 1].plot(t, values['tip_y_m']*1000, label=label, color=color, lw=1.1)
        axes[1, 0].plot(t, values['velocity_rms_m_s']*100, label=label, color=color, lw=1.1)
        axes[1, 1].plot(t, values['kinetic_j']*1e6, label=label, color=color, lw=1.1)
        if suffix:
            before = report['removed_kinetic_j']
            speed_before = np.sqrt(2*before/(.1*.75))
            axes[1, 0].plot([t[0], t[0]], [speed_before*100, 0], ':', color=color)
            axes[1, 1].plot([t[0], t[0]], [before*1e6, 0], ':', color=color)
        provenance['series'][name] = {'run': run.name, 'manifest_sha256': audit['manifest_sha256'],
            'verification_sha256': file_identity(verification)['sha256'],
            'removed_kinetic_j': report['removed_kinetic_j'],
            'velocity_rms_peak_m_s': float(values['velocity_rms_m_s'].max()),
            'absolute_tip_y_peak_m': float(abs(values['tip_y_m']).max())}
    axes[0, 1].set(title='자유단 중앙의 평면 밖 변위', ylabel='변위 (mm)')
    axes[1, 0].set(title='속도 초기화와 이후 응답', ylabel='자유 영역 속도 RMS (cm/s)')
    axes[1, 1].set(title='초기화 시 제거되는 운동에너지', ylabel='운동에너지 (µJ)')
    for ax in axes.flat:
        ax.set(xlabel='시각 (s)', xlim=(0, 1.5))
        ax.grid(alpha=.18)
        ax.legend(fontsize=8, loc='best')
    fig.suptitle(f"P3 랜덤 바람 · n{config['resolution']}, sub{config['substeps']} · 원식 검산 완료, 수렴 판정 별도", fontsize=12)
    args.output.mkdir(parents=True)
    for ext in ('png', 'pdf'):
        fig.savefig(args.output/('random_reset.'+ext), dpi=170)
    plt.close(fig)
    (args.output/'provenance.json').write_text(json.dumps(provenance, ensure_ascii=False, indent=2)+'\n')
    print('랜덤 바람·속도 초기화 진단 그림 저장 완료', flush=True)


if __name__ == '__main__':
    main()
