"""완료된 궤적만 읽는 GPU 검산 실행기. 기존 코드·검산 결과를 보존한다."""
import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from profile_run import digest

ADDITIONS = (
    'teacher/resident_audit.py','teacher/resident_audit_bounds.py','teacher/resident_audit_kernels.py',
    'teacher/resident_parallel_reductions.py','evaluation/teacher_gpu_audit_io.py','evaluation/teacher_resident_gpu_audit.py',
)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',type=Path,default=Path('experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_reuse_uncompressed_v1/candidate'))
    p.add_argument('--out',type=Path,default=Path('experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_audit_v1'))
    p.add_argument('--chunk-steps',type=int,default=64); p.add_argument('--prepare-only',action='store_true')
    args = p.parse_args()
    if args.chunk_steps < 1: p.error('--chunk-steps는 양수여야 합니다.')
    root = Path.cwd(); source = args.source.resolve().relative_to(root); out = args.out.resolve().relative_to(root)
    result = json.loads((source/'comparison.json').read_text())
    if result['status'] != 'passed': raise ValueError('기존 검산을 통과한 완료 실행이 필요합니다')
    manifest = json.loads((source/'manifest.json').read_text())
    for name,sha in manifest['files'].items():
        if digest(source/name) != sha: raise ValueError('기준 동결 파일 해시 불일치: '+name)
    for backend in ('gpu','hybrid'):
        for name,sha in result['backends'][backend]['files'].items():
            if digest(source/backend/name) != sha: raise ValueError('기준 결과 해시 불일치: '+backend+'/'+name)
    library = Path('experiments/artifacts/runs/teacher_timestep_search/gpu_resident_dependencies/cudss_0_7_1_6/nvidia/cu12/lib/libcudss.so.0')
    if digest(library) != result['backends']['gpu']['environment']['cudss_sha256']: raise ValueError('cuDSS 기준 해시 불일치')
    out.mkdir(parents=True,exist_ok=False)
    shutil.copytree(source/'runtime',out/'runtime')
    for name in ADDITIONS: shutil.copy2(Path('code/wind3dgs')/name,out/'runtime/code/wind3dgs'/name)
    shim = out/'runtime/native/libcudss_workspace.so'
    subprocess.run(['cc','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',str(out/'runtime/native/cudss_workspace.c'),'-o',str(shim),'-ldl','-pthread'],check=True)
    frozen = {str(path.relative_to(out)):digest(path) for path in sorted((out/'runtime').rglob('*')) if path.is_file() and '__pycache__' not in path.parts}
    metadata = {'scope':'기존 결과 GPU 재검산. 시뮬레이션·기준 검산 재실행 없음','source':str(source),
                'source_manifest_sha256':digest(source/'manifest.json'),'source_comparison_sha256':digest(source/'comparison.json'),
                'chunk_steps':args.chunk_steps,'files':frozen,'cudss_sha256':digest(library),'phase':'준비 완료'}
    def status(phase):
        metadata['phase'] = phase
        (out/'audit_run.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2)+'\n')
    status('준비 완료')
    if args.prepare_only:
        print('GPU 검산 준비 완료. 실행 시 새 --out 경로를 사용하세요.',flush=True); return
    for folder in Path('/proc').iterdir():
        if not folder.name.isdigit(): continue
        try: words = (folder/'cmdline').read_bytes().split(b'\0')
        except OSError: continue
        if b'-m' in words and any(w.startswith(b'wind3dgs.evaluation.teacher_') for w in words):
            raise RuntimeError('다른 teacher 실행이 있어 시작하지 않습니다. PID '+folder.name)
    env = os.environ.copy()
    env.update(PYTHONPATH=str((out/'runtime/code').resolve()),CUDSS_LIBRARY_PATH=str(library.resolve()),LD_PRELOAD=str(shim.resolve()),
               OPENBLAS_NUM_THREADS='1',OMP_NUM_THREADS='1',WIND3DGS_WORKSPACE=str(root),WARP_CACHE_PATH=str(root/'code/outputs/warp-cache'))
    command = [sys.executable,'-u','-m','wind3dgs.evaluation.teacher_resident_gpu_audit',str(source),'--out',str(out/'results'),'--chunk-steps',str(args.chunk_steps)]
    metadata['command'] = [Path(sys.executable).name,*command[1:]]
    try:
        status('GPU 검산 실행'); subprocess.run(command,env=env,check=True); status('검산 완료')
    except Exception:
        status('실패: 기존 결과 보존, 새 출력 경로로 재실행'); raise
    print('결과: '+str(out/'results/comparison.json'),flush=True)


if __name__ == '__main__': main()
