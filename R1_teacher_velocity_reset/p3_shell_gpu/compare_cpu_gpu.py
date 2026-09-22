"""완료된 동일 조건의 CPU/CUDA run을 원본 manifest와 연결해 사후 대조한다."""
from pathlib import Path
import argparse
import hashlib
import json

import numpy as np

from wind3dgs.evaluation.teacher_p3_shell import compare_wind
from wind3dgs.evaluation.teacher_p3_shell_comparison import interpolate_trace
from wind3dgs.evaluation.teacher_p3_shell_validation import read_run


def compare(cpu, gpu):
    a, at, ac, _ = read_run(cpu)
    b, bt, bc, _ = read_run(gpu)
    for key in ('law', 'material', 'policy', 'resolution', 'substeps', 'diagonal', 'reset_frame'):
        if ac[key] != bc[key]:
            raise ValueError('동일 조건 CPU/GPU 대조가 아닙니다: ' + key)
    if ac.get('initial_curvature', 0) != bc.get('initial_curvature', 0):
        raise ValueError('초기 형상 계열 불일치')
    if ac['environment']['device'] != 'cpu' or not bc['environment']['device'].startswith('cuda'):
        raise ValueError('실제 CPU 및 CUDA 원본이 필요합니다')
    for name, sha in ac['source_sha256'].items():
        if bc['source_sha256'].get(name) != sha:
            raise ValueError('공유 CPU 기준 source가 다릅니다: ' + name)
    np.testing.assert_array_equal(at['wind_m_s'], bt['wind_m_s'])
    np.testing.assert_array_equal(at['u_m'][0], bt['u_m'][0])
    traces = []
    defects = []
    for path, model, trace in ((cpu, a, at), (gpu, b, bt)):
        before = None
        if ac['reset_frame'] is not None:
            with np.load(path/'reset_event.npz', allow_pickle=False) as event:
                before = np.array(event['v_before_m_s'], copy=True)
        value, defect = interpolate_trace(model, trace, ac['substeps'], ac['substeps'],
                                          reset_frame=ac['reset_frame'], reset_velocity=before)
        traces.append(value)
        defects.append(defect)
    errors = compare_wind(a, traces[0], b, traces[1])
    for trace in traces:
        trace['u_m'] = trace['u_m'] - trace['u_m'][0]
    errors['delta_u_m'] = compare_wind(a, traces[0], b, traces[1])['u_m']
    limits = {'relative': 1e-6, 'displacement_absolute_m': 1e-9, 'velocity_absolute_m_s': 1e-7}
    passed = all(item['absolute_rms_peak'] <= (limits['velocity_absolute_m_s'] if key == 'v_m_s'
                 else limits['displacement_absolute_m']) + limits['relative']*item['reference_peak']
                 for key, item in errors.items())
    return {'cpu': cpu.name, 'gpu': gpu.name, 'passed': passed, 'cpu_gpu_errors_with_reset_left_limits': errors,
            'parity_policy': limits, 'kinematic_defect_rms_m_s': defects,
            'manifest_sha256': {p.name: hashlib.sha256((p/'manifest.json').read_bytes()).hexdigest()
                               for p in (cpu, gpu)},
            'wrapper_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'scope': '동일 grid의 모든 step 끝점과 reset 좌극한의 CPU/CUDA 구현 일치. Raw 수식 검산 및 물리 수렴은 별도',
            'generated_training_samples': 0, 'training_eligible': False, 'r1_complete': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('cpu', type=Path)
    parser.add_argument('gpu', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('기존 대조 결과를 덮어쓸 수 없습니다')
    value = compare(args.cpu, args.gpu)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    print('완료 CPU/CUDA 원본 대조:', value['passed'], flush=True)


if __name__ == '__main__':
    main()
