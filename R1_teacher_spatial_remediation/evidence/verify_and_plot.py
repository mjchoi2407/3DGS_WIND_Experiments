"""이 실험의 보존 artifact를 검산하고 compact evidence와 대표 그림을 생성한다."""
from pathlib import Path
import json
import os
import shutil
import sys

import numpy as np

WORKSPACE = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(WORKSPACE/'code'))
from wind3dgs.evaluation import teacher_plate_spatial_remediation as first
from wind3dgs.evaluation import teacher_plate_cubic_refinement as second

ROOT = WORKSPACE/'experiments/artifacts/runs/teacher_spatial_remediation'
EVIDENCE = Path(__file__).resolve().parent


def write(name, value):
    (EVIDENCE/name).write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False)+'\n', encoding='utf-8')


def collect():
    results = {}; inventory_comparisons = {}
    for family, verifier, stem in (('reference', first.verify, '20260908_reference_v1'),
                                    ('cubic', second.verify, '20260908_cubic_v1')):
        for suffix in ('', '_replay'):
            path = ROOT/(stem+suffix); key = family+suffix
            results[key] = verifier(path)
            results[key]['elapsed_s'] = json.loads((path/'runtime.json').read_text())['elapsed_s']
            manifest = json.loads((path/'manifest.json').read_text())
            results[key]['inventory_bytes'] = sum(x['bytes'] for x in manifest['outputs'].values())
            shutil.copyfile(path/'manifest.json', EVIDENCE/f'{key}_manifest.json')
        a = json.loads((ROOT/stem/'manifest.json').read_text())['outputs']
        b = json.loads((ROOT/(stem+'_replay')/'manifest.json').read_text())['outputs']
        if a.keys() != b.keys():
            raise ValueError('재실행 inventory 경로가 다릅니다')
        changed = [k for k in a if a[k] != b[k]]
        if changed != ['runtime.json']:
            raise ValueError(f'시간 외 재실행 값이 다릅니다: {changed}')
        inventory_comparisons[family] = {'identical_files': len(a)-1, 'differing_files': changed}
        for name in ('report.json', 'config.json', 'environment.json'):
            shutil.copyfile(ROOT/stem/name, EVIDENCE/f'{family}_{name}')
    # 선행 코드 30개와 원래 1,509 inventory도 현재 checkout에 대해 재검산한다.
    source = first.source_check(WORKSPACE/'experiments/artifacts/runs/teacher_shell_linear_spatial/20260908_reference_v1')
    write('verification.json', {'runs': results, 'replay_comparison': inventory_comparisons,
                                'original_source': source})
    spectral = {}
    for n in (4, 8, 16, 32):
        with np.load(ROOT/'20260908_reference_v1'/f'bspline_{n}.npz', allow_pickle=False) as a:
            omega, q0 = a['omega_rad_s'], a['q0']; energy = .5*(omega*q0)**2
            spectral[str(n)] = {'initial_energy_j': float(energy.sum()),
                'fraction_above_100_rad_s': float(energy[omega > 100].sum()/energy.sum()),
                'fraction_above_500_rad_s': float(energy[omega > 500].sum()/energy.sum())}
    write('initial_spectral_energy.json', spectral)
    return (json.loads((EVIDENCE/'reference_report.json').read_text()),
            json.loads((EVIDENCE/'cubic_report.json').read_text()))


def plot(first_report, cubic_report):
    os.environ.setdefault('MPLCONFIGDIR', str(WORKSPACE/'code/outputs/matplotlib-cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib import font_manager
    from matplotlib.ticker import NullFormatter
    fonts = {f.name for f in font_manager.fontManager.ttflist}
    if 'Noto Sans CJK JP' in fonts:
        plt.rcParams['font.family'] = 'Noto Sans CJK JP'
    plt.rcParams.update({'axes.unicode_minus': False, 'font.size': 10})
    fig, axes = plt.subplots(2, 2, figsize=(11, 7.5), layout='constrained')
    for row, condition in enumerate(('initial_x2', 'pressure_pulse')):
        before = {(r['left'], r['right']): r for r in first_report['comparisons'][condition]}
        after = {(r['left'], r['right']): r for r in cubic_report['comparisons'][condition]}
        for col, field in enumerate(('u', 'v')):
            ax = axes[row, col]
            values = [before[f'bspline_{a}', f'bspline_{b}'][field+'_exact']['normalized']*100 for a, b in ((4, 8), (8, 16), (16, 32))]
            ax.plot([8, 16, 32], values, 'o-', color='#0072B2', label='독립 B-spline')
            values = [before[f'p2_{a}_forward', f'p2_{b}_forward'][field+'_exact']['normalized']*100 for a, b in ((4, 8), (8, 16))]
            ax.plot([8, 16], values, 's-', color='#E69F00', label='P2 forward')
            rows = [after[f'p3_{a}_forward', f'p3_{b}_forward'][field] for a, b in ((4, 8), (8, 16))]
            measured = [r['normalized']*100 for r in rows]
            upper = [r['continuous_max_upper_normalized']*100 for r in rows]
            ax.plot([8, 16], measured, 'o-', color='#009E73', label='P3 forward')
            ax.fill_between([8, 16], measured, upper, color='#009E73', alpha=.16, label='P3 시간 최대값 상한까지')
            ax.plot([8, 16], upper, ':', color='#009E73')
            ax.axhline(1., color='#D55E00', linestyle='--', label='기존 1% 기준')
            ax.set(yscale='log', xscale='log', xticks=[8, 16, 32], xticklabels=['8', '16', '32'],
                xlabel='비교의 미세 격자 n (n/2 → n)', ylabel='정규화 위치 차이 [%]' if field == 'u' else '정규화 속도 차이 [%]',
                title=('x² 초기 변위' if row == 0 else '0.01Pa half-sine 처방 압력'))
            ax.grid(True, which='both', alpha=.18)
            ax.xaxis.set_minor_formatter(NullFormatter())
    axes[0, 0].legend(fontsize=8)
    fig.suptitle('같은 물성·위치 고정·분모·1% 기준의 공간 응답 비교\n압력 조건의 P3 통과와 x² 초기 상태의 속도 실패를 구분한다', fontsize=12)
    fig.savefig(EVIDENCE/'response_convergence.png', dpi=160)
    plt.close(fig)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.3), layout='constrained')
    with np.load(ROOT/'20260908_reference_v1/stencil_r1_n16_checkerboard.npz', allow_pickle=False) as a:
        values = np.ma.array(a['force_n'].reshape(17, 17)*1000, mask=~a['safe'].reshape(17, 17))
    im = axes[0].imshow(values, origin='lower', extent=[-1/32, 1+1/32, -1/32, 1+1/32], cmap='RdBu_r', vmin=-1., vmax=1., interpolation='nearest')
    axes[0].set(title='원래 checkerboard의 내부 굽힘력\n경계에 닿는 support는 표시에서 제외', xlabel='x [m]', ylabel='y [m]')
    axes[0].set_xlim(0, 1); axes[0].set_ylim(0, 1)
    fig.colorbar(im, ax=axes[0], label='법선 힘 [mN]')
    for diagonal, color in (('forward', '#0072B2'), ('checkerboard', '#D55E00')):
        rows = [r for r in first_report['stencil_diagnostics'] if r['minimum_rings'] == 1 and r['diagonal'] == diagonal]
        axes[1].plot([r['n'] for r in rows], [r['lowest_positive_omega_rad_s']['lumped'][1] for r in rows], 'o-', color=color, label=f'기존 {diagonal}')
    for label, report, key, ns, style in (
            ('독립 B-spline', first_report, 'bspline_{}', (4, 8, 16, 32), 'k--'),
            ('P3 checkerboard', cubic_report, 'p3_{}_checkerboard', (4, 8, 16), 's-')):
        values = [report['model_diagnostics'][key.format(n)]['lowest_positive_omega_rad_s'][1] for n in ns]
        axes[1].plot(ns, values, style, label=label, **({'color': '#009E73'} if label.startswith('P3') else {}))
    axes[1].set(xlabel='격자 n', ylabel='두 번째 양의 고유진동수 [rad/s]', title='대각선에 따른 저주파 차이와 수정 후보')
    axes[1].legend(fontsize=8); axes[1].grid(alpha=.2)
    fig.savefig(EVIDENCE/'interior_force_and_modes.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    plot(*collect())
    print('네 run의 inventory·재실행·원본 source 검산과 대표 그림 생성 완료')
