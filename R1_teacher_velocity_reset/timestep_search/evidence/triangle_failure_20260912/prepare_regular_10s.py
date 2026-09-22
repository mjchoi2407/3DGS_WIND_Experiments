"""검증한 삼각 깃발 입력·동결 코드를 보존 복사하여 새10초 실행을 준비한다."""
import copy
from pathlib import Path
import shutil

import numpy as np
from wind3dgs.evaluation.teacher_three_scene_run import digest, new_report, read, verify, write

source = Path('experiments/artifacts/runs/teacher_timestep_search/20260912_triangle_regular_01s_v1')
target = source.parent/'20260912_triangle_regular_10s_v1'
plan = verify(source)
assert read(source/'triangular_flag/report.json')['status'] == 'complete'
assert plan['frames'] == 6 and plan['shapes'] == ['triangular_flag']
checks = read(Path(__file__).parent/'regular_checks.json')
assert checks['manifest_sha256'] == digest(source/'manifest.json')
assert checks['report_sha256'] == digest(source/'triangular_flag/report.json')
assert checks['all_gpu_step_checks_passed'] and all(r['passed'] for r in checks['cpu_checks'])
expected = copy.deepcopy(plan)
expected['frames'] = 600
if target.exists():
    assert verify(target) == expected
    for name in ('triangular_flag.npz', 'wind.npz'):
        assert digest(target/'inputs'/name) == digest(source/'inputs'/name)
    print('기존10초 동결 묶음 검증 완료. 상태·결과를 초기화하지 않았습니다.')
else:
    with np.load(source/'inputs/wind.npz', allow_pickle=False) as z:
        assert len(z['wind_m_s']) >= 600
    target.mkdir()
    for path in [*sorted((source/'inputs').iterdir()), *sorted((source/'runtime').rglob('*.py'))]:
        destination = target/path.relative_to(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)
        assert digest(path) == digest(destination)
    write(target/'plan.json', expected)
    files = [target/'plan.json', *sorted((target/'inputs').iterdir()), *sorted((target/'runtime').rglob('*.py'))]
    write(target/'manifest.json', {str(p.relative_to(target)): digest(p) for p in files})
    write(target/'preparation.json', {
        'source': str(source), 'source_manifest_sha256': digest(source/'manifest.json'),
        'validation_sha256': digest(Path(__file__).parent/'regular_checks.json'),
        'preparation_script_sha256': digest(Path(__file__)),
        'changed_plan_fields': ['frames'], 'frames_before': 6, 'frames_after': 600,
        'initial_state': 'rest에서0초부터 시작; 단기 검증 궤적을 복사하지 않음',
        'scope': '삼각 깃발만10초. 완료한 직사각형·손수건과 옛 삼각 깃발 실패 원본 보존',
        'time_budget': '기존 삼각 깃발 정책 유지: 시간 한도 없음',
        'simulation_started': False,
    })
    write(target/'triangular_flag/report.json', new_report('triangular_flag'))
    assert verify(target) == expected
    print('새 삼각 깃발10초 실행 준비 완료. ready·0프레임, 계산 미시작.')
