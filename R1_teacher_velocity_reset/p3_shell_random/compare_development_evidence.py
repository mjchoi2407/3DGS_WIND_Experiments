"""완료된 동일 natural/reset 분기끼리 긴 수치 보간을 비교하는 실험 wrapper."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

from wind3dgs.evaluation.teacher_p3_shell_gpu import _redact


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('first', type=Path)
    parser.add_argument('second', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {'status': 'running', 'comparisons': {}, 'training_eligible': False, 'r1_complete': False,
              'generated_training_samples': 0, 'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    try:
        for name, suffix in [('natural', '')]+[(f'reset{c}', f'_reset{c}') for c in (18, 42, 66)]:
            paths = [p.with_name(p.name+suffix) for p in (args.first, args.second)]
            print('동일 분기 완료 대기:', name, flush=True)
            while not all((p/'manifest.json').exists() for p in paths):
                for p in paths:
                    if (p/'report.json').exists() and json.loads((p/'report.json').read_text())['status'] == 'failed':
                        raise ValueError('전진 실패 원본: '+p.name)
                time.sleep(5)
            output = args.output/(name+'.json')
            result = subprocess.run([sys.executable, '-u', '-m',
                'wind3dgs.evaluation.teacher_p3_shell_random_comparison', *map(str, paths), '--output', str(output)])
            if result.returncode:
                raise RuntimeError('비교 실패: '+name)
            value = json.loads(output.read_text())
            report['comparisons'][name] = value['interpolant_bounds']
            report[name+'_threshold_passed'] = value['interpolant_threshold_passed']
            print('분기 비교:', name, '속도 상대 상한', value['interpolant_bounds']['v_m_s']['relative_upper'], flush=True)
        report['status'] = 'completed'
        return 0
    except BaseException as error:
        report.update(status='failed', error={'type': type(error).__name__, 'message': _redact(str(error))})
        print('비교 묶음 실패:', _redact(str(error)), flush=True)
        return 1
    finally:
        (args.output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    raise SystemExit(main())
