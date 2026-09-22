import argparse
import hashlib
import json
from pathlib import Path

from wind3dgs.evaluation.teacher_p3_shell_random import QUALITY, file_identity, inspect_run, sources

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
if args.output.exists():
    parser.error('기존 요약을 덮어쓸 수 없습니다')
root = Path('experiments/artifacts/runs/teacher_p3_shell_random')
verification = root/'verification'
conditions = ('natural_m8_s128_v1', 'natural_m16_s128_v1', 'natural_m8_s256_v1',
              'natural_m16_s256_v1', 'natural_m16_s256_backward_v1')
comparisons = ('space8_16_s128_v2', 'space8_16_s256_v2', 'time8_s128_256_v2',
               'time16_s128_256_v2', 'direction16_s256_v2')
branches = ('natural', 'reset18', 'reset42', 'reset66')
report = {'conditions': {}, 'comparisons': {}, 'primary_verified_intervals': 0,
          'producer_source_sha256': sources(), 'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'development_checks_passed': True, **QUALITY,
          'scope': '지정한 약한 바람·고정 조건의 natural과 세 reset. 각 원본 hash/원식/수렴을 연결한 개발 검증; 독립 공간 기준·큰 변형·R1 전체 완료 아님'}
manifests = {}
for condition in conditions:
    folder = verification/condition
    assert json.loads((folder/'report.json').read_text())['status'] == 'completed', condition
    report['conditions'][condition] = {}
    for branch in branches:
        suffix = '' if branch == 'natural' else '_'+branch
        run = root/('20260909_'+condition+suffix)
        config, raw_report = inspect_run(run)
        assert config['source_sha256'] == sources()
        audit_path = folder/(branch+'.json')
        audit = json.loads(audit_path.read_text())
        assert audit['verified'] and audit['run'] == run.name
        assert audit['source_sha256'] == sources()
        digest = file_identity(run/'manifest.json')['sha256']
        assert digest == audit['manifest_sha256']
        if branch != 'natural':
            assert audit['parent_manifest_sha256'] == manifests['20260909_'+condition]
        manifests[run.name] = digest
        frames = audit['frame_results']
        geometry = all(f['bernstein_geometry']['global_injectivity_sufficient_condition'] for f in frames)
        row = {'run': run.name, 'manifest_sha256': digest, 'verification_sha256': file_identity(audit_path)['sha256'],
               'intervals': audit['verified_intervals'], 'elapsed_s': raw_report['elapsed_s'],
               'removed_kinetic_j': audit['removed_kinetic_j'],
               'max_nodal_displacement_m': max(f['max_nodal_displacement_m'] for f in frames),
               'max_force_residual_limit_ratio': max(f['max_force_residual_limit_ratio'] for f in frames),
               'min_area_ratio_lower': min(f['bernstein_geometry']['area_ratio_lower'] for f in frames),
               'max_strain_component_upper': max(f['bernstein_geometry']['strain_component_upper'] for f in frames),
               'max_linearized_fibre_strain_component_upper': max(f['bernstein_geometry']['linearized_fibre_strain_component_upper'] for f in frames),
               'zero_ambient_tail_work_j': sum(f['work_j'] for f in frames if f['frame'] >= 72),
               'max_absolute_energy_balance_j': max(abs(f['energy_balance_j']) for f in frames),
               'global_injectivity_sufficient_condition': geometry}
        report['conditions'][condition][branch] = row
        report['primary_verified_intervals'] += row['intervals']
        report['development_checks_passed'] &= geometry
    replay = json.loads((folder/'checkpoint42_replay.json').read_text())
    assert replay['step_diagnostics_exact'] and replay['arrays'] == 9
    checkpoint = json.loads((folder/'checkpoint42_raw.json').read_text())
    assert checkpoint['verified']
    checkpoint_run = root/checkpoint['run']
    checkpoint_config, _ = inspect_run(checkpoint_run)
    checkpoint_digest = file_identity(checkpoint_run/'manifest.json')['sha256']
    assert checkpoint_config['source_sha256'] == checkpoint['source_sha256'] == sources()
    assert checkpoint_digest == checkpoint['manifest_sha256'] == replay['manifest_sha256'][checkpoint_run.name]
    assert checkpoint['parent_manifest_sha256'] == manifests['20260909_'+condition]
    assert replay['manifest_sha256']['20260909_'+condition] == manifests['20260909_'+condition]
    report['conditions'][condition]['checkpoint_replay'] = replay
    print('요약 원본 연결:', condition, flush=True)
for comparison in comparisons:
    folder = verification/comparison
    assert json.loads((folder/'report.json').read_text())['status'] == 'completed'
    report['comparisons'][comparison] = {}
    for branch in branches:
        path = folder/(branch+'.json')
        value = json.loads(path.read_text())
        assert manifests[value['first']] == value['first_manifest_sha256']
        assert manifests[value['second']] == value['second_manifest_sha256']
        assert value['producer_source_sha256'] == sources()
        assert abs(value['norm']['reference_area_m2']-.75) < 1e-14
        report['comparisons'][comparison][branch] = {'bounds': value['interpolant_bounds'],
            'passed': value['interpolant_threshold_passed'], 'report_sha256': file_identity(path)['sha256']}
        report['development_checks_passed'] &= value['interpolant_threshold_passed']
qpath = verification/'natural_m16_s256_quadrature_v1.json'
q = json.loads(qpath.read_text())
assert q['manifest_sha256'] == manifests[q['run']]
assert q['producer_source_sha256'] == sources()
assert q['verification_sha256'] == file_identity(verification/'natural_m16_s256_v1'/'natural.json')['sha256']
report['selected_state_quadrature'] = {'maxima': q['maxima'], 'passed': q['selected_state_quadrature_passed'],
                                       'report_sha256': file_identity(qpath)['sha256']}
report['development_checks_passed'] &= q['selected_state_quadrature_passed']
assert report['primary_verified_intervals'] == 239616
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open('x') as stream:
    json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write('\n')
print('개발 검증 요약:', report['development_checks_passed'], '구간', report['primary_verified_intervals'], '/ 추가학습데이터0', flush=True)
