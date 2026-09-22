"""저장된 v2/기존 OFF 결과만 읽어 비용을 집계한다. 시뮬레이션·GPU 초기화 없음."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


ON = Path('experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_v2')
OFF = Path('experiments/artifacts/runs/teacher_timestep_search/newmark_dt_gauss_retry_bend500_v1')
HERE = Path('experiments/R1_teacher_velocity_reset/self_contact')
SAMPLES = HERE / 'refined_gpu_checks/strength_report.json'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, default=HERE / 'cost_report.json')
    args = parser.parse_args()
    if args.out.exists():
        raise FileExistsError('기존 비용 집계는 덮어쓰지 않습니다. 새 --out을 지정하세요')
    sources = {}

    def digest(path):
        value = hashlib.sha256(path.read_bytes()).hexdigest()
        sources[str(path)] = value
        return value

    def read(path):
        digest(path)
        return json.loads(path.read_text())

    def timing(path):
        digest(path)
        return [json.loads(line) for line in path.read_text().splitlines()]

    def comparison(old, new):
        return dict(off_s=old, on_s=new, added_s=new-old,
                    time_ratio=new/old, increase_percent=100*(new/old-1))

    manifest = read(ON / 'manifest.json')
    for name, sha in manifest.items():
        # runtime 전체 hash는 검증하지만 큰 목록은 원본 manifest가 소유한다.
        assert hashlib.sha256((ON/name).read_bytes()).hexdigest() == sha, name
    inputs = read(ON / 'reference_inputs.json')
    cfg = read(ON / 'suite.json')
    scenes, memory = [], []
    for shape in cfg['shapes']:
        for name, sha in inputs[shape].items():
            assert digest(OFF/shape/name) == sha, (shape, name)
            assert digest(ON/shape/name) == sha, (shape, name)
        old = timing(OFF/shape/'preload'/shape/'frame_timings.jsonl')[0]
        report = read(ON/shape/'checks/smoke/preload/report.json')
        initial = read(ON/shape/'checks/preflight/report.json')['initial_contact']
        assert report['status'] == 'complete' and report['source_frame'] == 0
        assert old['frame'] == 0 and old['accepted_steps'] == 64
        assert old['gauss_retries'] == old['half_dt_retries'] == 0
        assert report['frames'][0]['flags'] == [0]
        scenes.append(dict(shape=shape, phase='preload', frames=1, substeps=64,
            **comparison(old['compute_audit_s'], report['frames'][0]['compute_audit_s']),
            on_setup_s=report['setup_s'], initial_contact_energy_j=initial['energy_j'],
            on_refined_substeps=report['frames'][0]['refined_substeps'],
            solver_counts_first16_match=old['attempts'][0]['counts'][:16] == report['frames'][0]['counts'][:16]))
        # GPUShellContact 두 개(풀이/독립 검산)의 명시적 주요 배열만 계산한다.
        capacity = max(4096, 32*initial['proxy_vertices'])
        elements = initial['proxy_faces'] // cfg['contact_policy']['subdivisions']**2
        queue_capacity = max(1024, 8*elements)
        memory.append(dict(shape=shape, active_capacity_each=capacity,
            hessian_two_objects_bytes=2*capacity*12*12*8,
            geometry_two_queues_bytes=2*queue_capacity*18*2*3*8,
            scope='명시적 주요 배열 크기; BVH/gradient/trace/allocator/cuDSS 제외, GPU 메모리 실측 아님'))

    prefix = read(ON/'reference_rectangle/outputs/preload/report.json')
    assert prefix['status'] == 'interrupted'
    frames = prefix['frames']; n = len(frames)
    original = OFF/'reference_rectangle/preload/reference_rectangle'
    old_frames = timing(original/'frame_timings.jsonl')[:n]
    assert n > 0 and len(old_frames) == n
    max_error = {k: 0. for k in ('u_hi', 'u_lo', 'v_hi', 'v_lo')}
    force_error = 0.; flags_ok = True
    digest(original/'chunks/0000.npz'); digest(original/'chunks/0000.audit.npz')
    with np.load(original/'chunks/0000.npz') as old:
        for i, frame in enumerate(frames):
            path = ON/'reference_rectangle/outputs/preload'/f'frame_{i:04d}.npz'
            assert digest(path) == frame['state_sha256']
            with np.load(path) as state:
                flags_ok &= not np.any(state['flags'])
                for key in max_error:
                    max_error[key] = max(max_error[key], float(np.max(abs(state[key]-old[key][i+1]))))
                force_error = max(force_error, float(np.max(abs(state['held_force_n']-old['held_force_n'][i]))))
    with np.load(original/'chunks/0000.audit.npz') as audit:
        assert np.all(audit['method'][:64*n] == 0) and not np.any(audit['flags'][:64*n])
    # ON 카운터는 누적값, OFF timing은 프레임별 값이다. 차분한 뒤 비교한다.
    iterations = np.diff([0]+[f['counts'][9] for f in frames])
    builds = np.diff([0]+[f['counts'][15] for f in frames])
    prefix_report = dict(shape='reference_rectangle', frames=n, substeps=64*n,
        **comparison(sum(f['compute_audit_s'] for f in old_frames), sum(f['compute_audit_s'] for f in frames)),
        on_frame_min_s=min(f['compute_audit_s'] for f in frames),
        on_frame_max_s=max(f['compute_audit_s'] for f in frames),
        raw_max_abs_difference=max_error, held_force_max_abs_difference_n=force_error,
        all_saved_flags_zero=bool(flags_ok),
        gmres_iterations_match=bool(np.array_equal(iterations, [f['gmres_iterations'] for f in old_frames])),
        matrix_rebuilds_match=bool(np.array_equal(builds, [f['matrix_rebuilds'] for f in old_frames])),
        on_refined_substeps=sum(f['refined_substeps'] for f in frames),
        full_trajectory_verified=False)

    cpu = read(HERE/'barrier_1000_report.json')
    cases = {c['case']: c for c in cpu['cases']}
    cpu_comparison = []
    for name in ('face_approach', 'edge_crossing', 'fast_approach'):
        off, on = cases[name+'_off_lbvh'], cases[name+'_on_lbvh']
        assert off['completed'] and on['completed'] and off['accepted_substeps'] == on['accepted_substeps']
        cpu_comparison.append(dict(case=name, steps=on['accepted_substeps'],
            **comparison(off['elapsed_s'], on['elapsed_s']), scope='CPU 풀이만; 사후 독립 검산 제외'))
    samples = read(SAMPLES)
    sample_cost = [dict(name=c['name'], steps=c['steps'], solve_s=c['gpu_solve_s'],
        audit_s=c['gpu_audit_s'], setup_s=c['setup_s'],
        total_compute_s=c['gpu_solve_s']+c['gpu_audit_s'],
        audit_share_percent=100*c['gpu_audit_s']/(c['gpu_solve_s']+c['gpu_audit_s'])) for c in samples['cases']]
    for name in ('gpu_shell_contact.py', 'resident_contact_stepper.py', 'resident_metric_certificate.py'):
        digest(ON/'runtime/wind3dgs/teacher'/name)
    report = dict(schema='p3_contact_saved_cost_v1', measured_new_gpu_work=False,
        scope='과거 저장 결과의 비동시 비교; GPU 공유 부하·실행기 차이가 섞여 순수 접촉 증가율 미확정',
        input_hashes_match=True, gpu_preload_first_frame=scenes, gpu_rectangle_prefix=prefix_report,
        cpu_solve_only=cpu_comparison, gpu_contact_sample_cost=sample_cost,
        cpu_broad_phase=cpu['broadphase'], main_buffer_estimates=memory,
        stage_profile_available=False, training_eligible=False, source_sha256=sources)
    digest(Path(__file__).relative_to(Path.cwd()) if Path(__file__).is_absolute() else Path(__file__))
    with args.out.open('x') as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2); handle.write('\n')
    print(f'저장 결과 비용 집계 완료: GPU 계산 없이 {n}프레임·세 씬 초기 프레임 비교')


if __name__ == '__main__':
    main()
