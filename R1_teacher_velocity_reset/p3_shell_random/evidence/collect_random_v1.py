"""완결된 랜덤 바람 개발 검증의 작은 원본·검산·재현 근거를 선별 보존한다."""
import hashlib
import json
from pathlib import Path

workspace = Path.cwd()
raw = workspace/'experiments/artifacts/runs/teacher_p3_shell_random'
evidence = workspace/'experiments/R1_teacher_velocity_reset/p3_shell_random/evidence'
summary = json.loads((raw/'verification/final_summary_v1.json').read_text())
assert summary['development_checks_passed'] and summary['generated_training_samples'] == 0

def copy_once(source, target):
    data = source.read_bytes()
    if b'/' + b'home/' in data or b'/' + b'root/' in data:
        raise ValueError('개인 절대 경로 검사: '+str(source.relative_to(workspace)))
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != data:
            raise ValueError('기존 evidence와 불일치: '+str(target.relative_to(workspace)))
    else:
        target.write_bytes(data)

runs = []
for run in sorted(raw.glob('20260909_*')):
    if not (run/'manifest.json').exists():
        continue
    report = json.loads((run/'report.json').read_text())
    assert report['status'] == 'completed', run.name
    for name in ('config.json', 'report.json', 'manifest.json', 'console.log'):
        copy_once(run/name, evidence/run.name/name)
    runs.append(run.name)
for source in sorted((raw/'verification').rglob('*')):
    if source.is_file() and source.suffix in ('.json', '.log'):
        copy_once(source, evidence/source.relative_to(raw))
copy_once(Path(__file__), evidence/'collect_random_v1.py')
copy_once(Path(__file__).with_name('aggregate_random_v1.py'), evidence/'aggregate_random_v1.py')
log=Path(__file__).with_name('random_quadrature_v1.log')
copy_once(log,evidence/'tests/random_quadrature_v1.log')
files = {}
for f in sorted(evidence.rglob('*')):
    if f.is_file() and not f.name.startswith('inventory_'):
        data = f.read_bytes()
        files[f.relative_to(evidence).as_posix()] = {'size_bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
with (evidence/'inventory_v1.json').open('x') as stream:
    json.dump({'files': files, 'complete_raw_runs': runs, 'raw_npz_included': False,
               'source': 'experiments/artifacts/runs/teacher_p3_shell_random',
               'scope': '완결 원본 metadata와 검산, 재현 source. v1 비교 wrapper 제어 중단 기록도 포함하며 solver 실패와 구분한다'}, stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print('작은 근거 보존:',len(runs),'원본 /',len(files),'파일 / 원본 NPZ 별도 보존',flush=True)
