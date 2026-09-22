"""선택한 natural 원본을 기다려 검산·checkpoint replay·세 reset 분기를 실행하는 실험 wrapper."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import numpy as np

from wind3dgs.evaluation.teacher_p3_shell_gpu import _redact
from wind3dgs.evaluation.teacher_p3_shell_random import QUALITY, file_identity, inspect_run, sources
from wind3dgs.evaluation.teacher_p3_shell_random_validation import load_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('natural', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    report = {'status': 'running', 'natural': args.natural.name, 'steps': [], **QUALITY,
              'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    expected = sources()
    with (args.output/'console.log').open('x') as log:
        def say(message):
            line = _redact(str(message))
            print(line, flush=True)
            log.write(line+'\n')
            log.flush()

        def execute(module, arguments):
            if expected != sources():
                raise ValueError('진행 중 source가 바뀌었습니다')
            process = subprocess.Popen([sys.executable, '-u', '-m', module, *map(str, arguments)],
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            for line in process.stdout:
                say(line.rstrip('\n'))
            if process.wait():
                raise RuntimeError('실행/검산 실패: '+module)

        def verify(run, name):
            execute('wind3dgs.evaluation.teacher_p3_shell_random_validation',
                    [run, '--device', 'cuda:0', '--output', args.output/(name+'.json')])
            report['steps'].append(name)

        try:
            say('Natural 완료 대기: '+args.natural.name)
            while not (args.natural/'manifest.json').exists():
                if (args.natural/'report.json').exists():
                    current = json.loads((args.natural/'report.json').read_text())
                    if current['status'] == 'failed':
                        raise ValueError('Natural 전진 실패: '+args.natural.name)
                time.sleep(5)
            config, _ = inspect_run(args.natural)
            verify(args.natural, 'natural')
            common = ['--resolution', config['resolution'], '--substeps', config['substeps'],
                      '--compute-backend', config.get('compute_backend', 'reference'),
                      '--wind-scale', config['wind_scale'],
                      '--diagonal', config['diagonal'], '--parent', args.natural, '--device', 'cuda:0']
            replay = args.natural.with_name(args.natural.name+'_checkpoint42_replay')
            execute('wind3dgs.evaluation.teacher_p3_shell_random',
                    [*common, '--checkpoint', 42, '--replay-checkpoint', '--end-frame', 43, '--output', replay])
            verify(replay, 'checkpoint42_raw')
            original, original_steps = load_frame(args.natural, 42)
            repeated, repeated_steps = load_frame(replay, 42)
            assert set(original) == set(repeated)
            for key in original:
                np.testing.assert_array_equal(original[key], repeated[key])
            assert original_steps == repeated_steps
            result = {'arrays': len(original), 'scalars': sum(v.size for v in original.values()),
                      'step_diagnostics_exact': True,
                      'manifest_sha256': {p.name: file_identity(p/'manifest.json')['sha256'] for p in (args.natural, replay)}}
            (args.output/'checkpoint42_replay.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n')
            say('Checkpoint42 저장 재시작의 모든 배열/step diagnostics 정확히 일치')
            for checkpoint in (18, 42, 66):
                branch = args.natural.with_name(args.natural.name+f'_reset{checkpoint}')
                execute('wind3dgs.evaluation.teacher_p3_shell_random',
                        [*common, '--checkpoint', checkpoint, '--output', branch])
                verify(branch, f'reset{checkpoint}')
            report['status'] = 'completed'
            return 0
        except BaseException as error:
            report.update(status='failed', error={'type': type(error).__name__, 'message': _redact(str(error))})
            say('랜덤 바람 검증 묶음 실패: '+str(error))
            return 1
        finally:
            (args.output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
            say('랜덤 바람 검증 묶음 종료: '+report['status']+' / 추가 학습데이터0')


if __name__ == '__main__':
    raise SystemExit(main())
