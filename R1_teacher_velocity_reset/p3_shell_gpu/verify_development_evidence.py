"""고정된 GPU 수식 진단 묶음을 CPU 원식으로 검산한다. Dataset은 발행하지 않는다."""
from pathlib import Path
import argparse
import hashlib
import json
import time

import numpy as np

from wind3dgs.evaluation.teacher_p3_shell_validation import verify_wind, validation_sources, read_run
from wind3dgs.evaluation.teacher_p3_shell_comparison import compare_interpolants


NAMES = (
    '20260909_strong_reset_m16_s128_v2',
    '20260909_weak_m32_s128_v2',
    '20260909_strong_reset_m32_s128_v3',
    '20260909_strong_reset_m32_s256_v3',
    '20260909_strong_reset_m16_s128_v3',
    '20260909_strong_reset_m16_s128_replay_v3',
)


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


def replay(first, second):
    _, a, ac, _ = read_run(first)
    _, b, bc, _ = read_run(second)
    for key in ('law', 'material', 'policy', 'source_sha256', 'resolution', 'substeps',
                'diagonal', 'reset_frame', 'reference_cpu_manifest_sha256'):
        if ac[key] != bc[key]:
            raise ValueError('재실행 identity 불일치: ' + key)
    pairs = [('trace', a, b)]
    with np.load(first/'reset_event.npz', allow_pickle=False) as x, np.load(second/'reset_event.npz', allow_pickle=False) as y:
        pairs.append(('reset_event', dict(x), dict(y)))
    arrays = scalars = 0
    for _, x, y in pairs:
        if x.keys() != y.keys():
            raise ValueError('재실행 배열 집합 불일치')
        for name in x:
            if x[name].dtype != y[name].dtype:
                raise ValueError('재실행 dtype 불일치: ' + name)
            np.testing.assert_array_equal(x[name], y[name])
            arrays += 1
            scalars += x[name].size
    if json.loads((first/'step_diagnostics.json').read_text()) != json.loads((second/'step_diagnostics.json').read_text()):
        raise ValueError('재실행 step diagnostics 불일치')
    return {'exact_arrays': arrays, 'exact_scalars': scalars, 'step_diagnostics_exact': True,
            'first': first.name, 'second': second.name,
            'manifest_sha256': {p.name: hashlib.sha256((p/'manifest.json').read_bytes()).hexdigest()
                               for p in (first, second)}}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('experiments/artifacts/runs/teacher_p3_shell_gpu'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    source = validation_sources()
    pending = [args.root/name for name in NAMES]
    while pending:
        ready = [p for p in pending if (p/'manifest.json').exists()]
        if not ready:
            time.sleep(5)
            continue
        for path in ready:
            if source != validation_sources():
                raise ValueError('검산 중 CPU source 변경')
            result = verify_wind(path)
            write(args.output/(path.name+'.json'), result)
            pending.remove(path)
            print('GPU 원본의 CPU 수식 검산 완료:', path.name, '/ 남은 실행', len(pending), flush=True)
    pairs = (
        ('strong_space16_32', NAMES[4], NAMES[2]),
        ('strong_time32', NAMES[2], NAMES[3]),
    )
    comparisons = {}
    for label, first, second in pairs:
        result = compare_interpolants(args.root/first, args.root/second)
        write(args.output/(label+'_interpolant.json'), result)
        comparisons[label] = result['interpolant_bounds']
        print('GPU 수치 보간 수렴 상한:', label, result['interpolant_threshold_passed'], flush=True)
    repeated = replay(args.root/NAMES[4], args.root/NAMES[5])
    write(args.output/'replay.json', repeated)
    write(args.output/'summary.json', {'verified_runs': list(NAMES), 'comparisons': comparisons,
          'replay': repeated, 'validation_source_sha256': source,
          'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
          'generated_training_samples': 0, 'training_eligible': False, 'r1_complete': False})
    print('GPU 수식 진단 묶음 검산 종료', flush=True)


if __name__ == '__main__':
    main()
