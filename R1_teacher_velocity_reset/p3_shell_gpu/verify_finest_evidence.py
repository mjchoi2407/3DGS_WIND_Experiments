"""GPU finest 공간/시간/대각선 비교를 추가 검산한다. 기존 원본은 변경하지 않는다."""
from pathlib import Path
import argparse
import hashlib
import time

from verify_development_evidence import write
from wind3dgs.evaluation.teacher_p3_shell_validation import verify_wind, validation_sources
from wind3dgs.evaluation.teacher_p3_shell_comparison import compare_interpolants


NAMES = (
    '20260909_strong_reset_m16_s256_v3',
    '20260909_strong_reset_m32_s256_backward_v3',
    '20260909_weak_m32_s256_v3',
    '20260909_weak_m32_s256_backward_v3',
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('experiments/artifacts/runs/teacher_p3_shell_gpu'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    sources = validation_sources()
    pending = [args.root/name for name in NAMES]
    while pending:
        ready = [p for p in pending if (p/'manifest.json').exists()]
        if not ready:
            time.sleep(5)
            continue
        for path in ready:
            if validation_sources() != sources:
                raise ValueError('검산 중 CPU source 변경')
            write(args.output/(path.name+'.json'), verify_wind(path))
            pending.remove(path)
            print('Finest GPU 원본의 CPU 검산 완료:', path.name, flush=True)
    pairs = (
        ('strong_space16_32_finer_time', NAMES[0], '20260909_strong_reset_m32_s256_v3'),
        ('strong_direction32', '20260909_strong_reset_m32_s256_v3', NAMES[1]),
        ('weak_direction32', NAMES[2], NAMES[3]),
    )
    comparisons = {}
    for label, first, second in pairs:
        value = compare_interpolants(args.root/first, args.root/second)
        write(args.output/(label+'_interpolant.json'), value)
        comparisons[label] = value['interpolant_bounds']
        print('Finest GPU 수렴 상한:', label, value['interpolant_threshold_passed'], flush=True)
    write(args.output/'summary.json', {'verified_runs': list(NAMES), 'comparisons': comparisons,
          'validation_source_sha256': sources,
          'wrapper_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                             for p in (Path(__file__), Path(__file__).with_name('verify_development_evidence.py'))},
          'training_eligible': False, 'r1_complete': False, 'generated_training_samples': 0})
    print('Finest GPU 추가 검산 종료', flush=True)


if __name__ == '__main__':
    main()
