"""완료 비교의 동결 GPU worker만 Nsight Systems로 재실행하는 실험 wrapper."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


def digest(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--baseline', type=Path, default=Path('experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_resident_10frames_v1'))
    parser.add_argument('--out', type=Path, default=Path('experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_profile_v1'))
    parser.add_argument('--prepare-only', action='store_true')
    parser.add_argument('--internal', action='store_true', help='Nsight 대신 GPU timestamp 사용')
    parser.add_argument('--parallel', action='store_true', help='병렬 합산, 계측 없음')
    parser.add_argument('--gpu-only', action='store_true', help='기존 GPU, 계측 없음')
    parser.add_argument('--preconditioner', action='store_true', help='병렬 합산+보조 행렬 적용 개선')
    parser.add_argument('--reuse-audit', action='store_true', help='기준 검산 재사용, 새 GPU만 검산')
    parser.add_argument('--legacy-audit', action='store_true', help='GPU 상주 검산 대신 기존 CPU/GPU 검산 사용')
    parser.add_argument('--audit-chunk-steps', type=int, default=64, help='GPU 검산 메모리에 담을 단계 수')
    parser.add_argument('--current-first', action='store_true', help='매 프레임 current로 시작')
    parser.add_argument('--reuse-uncompressed', action='store_true', help='채택 평가 재사용+무압축 기록')
    args = parser.parse_args()
    if sum((args.internal, args.parallel, args.gpu_only, args.preconditioner, args.current_first, args.reuse_uncompressed)) > 1:
        parser.error('계측/병렬/기존 GPU 모드는 하나만 선택하세요.')
    local_run = args.internal or args.parallel or args.gpu_only or args.preconditioner or args.current_first or args.reuse_uncompressed
    base, out = args.baseline, args.out
    if not local_run and not shutil.which('nsys'):
        raise RuntimeError('nsys가 필요합니다. 자동 설치하지 않습니다.')
    result = json.loads((base/'comparison.json').read_text())
    if result['status'] != 'passed':
        raise RuntimeError('검산을 통과한 기준 실행이 필요합니다.')
    if not local_run and 'microsoft' in os.uname().release.lower() and result['backends']['gpu']['environment']['gpu'] == 'NVIDIA GeForce GTX 1080 Ti':
        raise RuntimeError('GTX 1080 Ti+WSL의 Nsight 추적은 지원 범위 밖입니다. run_gpu_resident_timing.sh를 사용하세요.')
    manifest = json.loads((base/'manifest.json').read_text())
    for name, expected in manifest['files'].items():
        if digest(base/name) != expected:
            raise RuntimeError('기준 동결 파일 불일치: '+name)
    for backend in ('hybrid', 'gpu'):
        for name, expected in result['backends'][backend]['files'].items():
            if digest(base/backend/name) != expected:
                raise RuntimeError('기준 결과 해시 불일치: '+backend+'/'+name)
    # 독립 복사: 검산이 hybrid/audit.json을 써도 기준 실행에는 영향이 없다.
    out.mkdir(parents=True, exist_ok=False)
    for name in ('runtime', 'fixture', 'hybrid'):
        shutil.copytree(base/name, out/name)
    shutil.copy2(base/'manifest.json', out/'manifest.json')
    additions=[]
    if args.internal:additions += ['teacher/resident_timing.py', 'evaluation/teacher_gpu_timed_worker.py']
    if args.parallel or args.preconditioner or args.current_first or args.reuse_uncompressed:additions += ['teacher/resident_parallel_reductions.py', 'evaluation/teacher_gpu_parallel_worker.py']
    if args.preconditioner or args.current_first or args.reuse_uncompressed:additions += ['teacher/resident_preconditioner_reuse.py', 'evaluation/teacher_gpu_preconditioner_worker.py']
    if args.current_first or args.reuse_uncompressed:additions += ['teacher/resident_current_first.py','evaluation/teacher_gpu_current_first_worker.py']
    if args.reuse_uncompressed:additions += ['teacher/resident_accepted_evaluation.py','teacher/resident_uncompressed_recording.py','evaluation/teacher_gpu_reuse_uncompressed_worker.py']
    if args.reuse_audit:
        additions += ['evaluation/teacher_cached_gpu_audit.py']
        if not args.legacy_audit:
            from audit_run import ADDITIONS
            additions += list(ADDITIONS)
        shutil.copy2(base/'comparison.json',out/'cached_baseline.json')
        manifest['files']['cached_baseline.json']=digest(out/'cached_baseline.json')
    for name in additions:
        target=out/'runtime/code/wind3dgs'/name
        shutil.copy2(Path('code/wind3dgs')/name,target)
        manifest['files'][str(target.relative_to(out))]=digest(target)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    library = Path('experiments/artifacts/runs/teacher_timestep_search/gpu_resident_dependencies/cudss_0_7_1_6/nvidia/cu12/lib/libcudss.so.0')
    if digest(library) != result['backends']['gpu']['environment']['cudss_sha256']:
        raise RuntimeError('cuDSS 기준 해시 불일치')
    shim = out/'runtime/native/libcudss_workspace.so'
    subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-Wall', '-Wextra', '-Werror', str(out/'runtime/native/cudss_workspace.c'), '-o', str(shim), '-ldl', '-pthread'], check=True)
    metadata = {'baseline': str(base), 'baseline_manifest_sha256': digest(base/'manifest.json'),
                'baseline_result_sha256': digest(base/'comparison.json'),
                'nsys_version': None if local_run else subprocess.check_output(['nsys', '--version'], text=True).strip(),
                'scope': '동결 GPU 10프레임: '+('채택 평가 재사용+무압축 기록' if args.reuse_uncompressed else '매 프레임 current 시작' if args.current_first else '보조 행렬 적용 개선' if args.preconditioner else '병렬 합산' if args.parallel else '기존 GPU' if args.gpu_only else '내부 계측' if args.internal else 'Nsight'),
                'performance_claim': False, 'phase': '준비 완료'}
    def status(phase):
        metadata['phase'] = phase
        (out/'profile_status.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2)+'\n')
    status('준비 완료')
    if args.prepare_only:
        print('준비 검증 완료. 실행할 때는 새 --out 경로를 사용하세요.', flush=True)
        return
    env = os.environ.copy()
    env.update(PYTHONPATH=str((out/'runtime/code').resolve()), CUDSS_LIBRARY_PATH=str(library.resolve()),
               LD_PRELOAD=str(shim.resolve()), OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1',
               WIND3DGS_WORKSPACE=str(Path.cwd()), WARP_CACHE_PATH=str(Path('code/outputs/warp-cache').resolve()))
    for folder in Path('/proc').iterdir():
        if not folder.name.isdigit():
            continue
        try:
            words = (folder/'cmdline').read_bytes().split(b'\0')
        except OSError:
            continue
        if b'-m' in words and any(w.startswith(b'wind3dgs.evaluation.teacher_') for w in words):
            raise RuntimeError('다른 teacher 실행이 있어 시작하지 않습니다. PID '+folder.name)
    worker = [sys.executable, '-u', '-m', 'wind3dgs.evaluation.teacher_gpu_comparison', str(out)]
    command = ['nsys', 'profile', '--trace=cuda,nvtx', '--sample=none', '--cpuctxsw=none',
               '--cuda-graph-trace=node', '--force-overwrite=false', '-o', str(out/'gpu_trace'),
               *worker, '--worker', 'gpu']
    if args.internal:
        command = [sys.executable, '-u', '-m', 'wind3dgs.evaluation.teacher_gpu_timed_worker', str(out)]
    if args.parallel:
        command = [sys.executable, '-u', '-m', 'wind3dgs.evaluation.teacher_gpu_parallel_worker', str(out)]
    elif args.preconditioner:
        command = [sys.executable, '-u', '-m', 'wind3dgs.evaluation.teacher_gpu_preconditioner_worker', str(out)]
    elif args.current_first:
        command = [sys.executable, '-u', '-m', 'wind3dgs.evaluation.teacher_gpu_current_first_worker', str(out)]
    elif args.reuse_uncompressed:
        command = [sys.executable, '-u', '-m', 'wind3dgs.evaluation.teacher_gpu_reuse_uncompressed_worker', str(out)]
    elif args.gpu_only:
        command = [*worker, '--worker', 'gpu']
    metadata['command'] = command
    try:
        status('GPU 추적 실행')
        subprocess.run(command, env=env, check=True)
        status('추적 밖 독립 검산')
        audit_command = [sys.executable, '-u', '-m', 'wind3dgs.evaluation.teacher_cached_gpu_audit', str(out)] if args.reuse_audit else [*worker, '--audit']
        if args.reuse_audit and not args.legacy_audit:
            audit_command = [sys.executable, '-u', '-m', 'wind3dgs.evaluation.teacher_resident_gpu_audit', str(out), '--chunk-steps', str(args.audit_chunk_steps)]
        subprocess.run(audit_command, env=env, check=True)
        # 기존 감사기는 시간 비율도 계산한다. 추적 실행에서는 성능 근거로 발행하지 않는다.
        path = out/'comparison.json'
        checked = json.loads(path.read_text())
        checked.update(generation_speedup=None, compute_and_buffer_speedup=None,
                       profiling_run=not (args.parallel or args.gpu_only or args.preconditioner or args.current_first or args.reuse_uncompressed), timing_comparable=False)
        path.write_text(json.dumps(checked, ensure_ascii=False, indent=2)+'\n')
        if not local_run:
            status('커널·메모리·CUDA API 통계 생성')
            with (out/'nsys_stats.txt').open('w') as stream:
                subprocess.run(['nsys', 'stats', '--report', 'cuda_gpu_kern_sum,cuda_gpu_mem_time_sum,cuda_api_sum', str(out/'gpu_trace.nsys-rep')], stdout=stream, stderr=subprocess.STDOUT, check=True)
        elif args.internal:
            timing = json.loads((out/'gpu_timing.json').read_text())
            roots = [r for r in timing['regions'] if '/' not in r['path']]
            if not any(r['path'].endswith('._step') and r['calls'] == 640 and r['inclusive_s'] > 0 for r in roots):
                raise RuntimeError('640단계 시간 기록 검증 실패')
        status('계산·검산 완료' if args.parallel or args.gpu_only or args.preconditioner or args.current_first or args.reuse_uncompressed else '추적·검산·통계 완료')
        print('완료: 병렬화 비교는 상위 summary.json을 확인합니다. 내부 계측은 gpu_timing.json, Nsight는 nsys_stats.txt를 분석합니다. 시간 비율은 성능 근거로 사용하지 않습니다.', flush=True)
    except Exception:
        status('실패: 로그 확인, 재실행은 새 출력 경로 사용')
        raise


if __name__ == '__main__':
    main()
