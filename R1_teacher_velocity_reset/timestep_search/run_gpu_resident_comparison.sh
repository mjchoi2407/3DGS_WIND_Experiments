#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
mode=run
out=experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_resident_10frames_v1
config=experiments/R1_teacher_velocity_reset/timestep_search/gpu_resident/comparison.json
python_bin="${WIND3DGS_PYTHON:-.venv/bin/python}"
while (($#)); do
  case "$1" in
    --prepare-only|--background|--logs|--status-only)
      [[ "$mode" == run ]] || { printf '%s\n' '실행 모드는 한 번만 지정하세요.' >&2; exit 2; }
      mode="$1";shift ;;
    --out|--config)
      (($# >= 2)) || { printf '%s\n' '옵션 뒤에 경로가 필요합니다.' >&2; exit 2; }
      if [[ "$1" == --out ]]; then out="$2";else config="$2";fi;shift 2 ;;
    -h|--help)
      printf '%s\n' '사용법: run_gpu_resident_comparison.sh [--prepare-only|--background|--logs|--status-only] [--out 새_결과_경로] [--config 설정_JSON]';exit 0 ;;
    *) printf '알 수 없는 옵션: %s\n' "$1" >&2;exit 2 ;;
  esac
done
if [[ "$mode" == --logs ]]; then exec tail -n 50 -F "$out/comparison.log";fi
if [[ "$mode" == --status-only ]]; then
  "$python_bin" - "$out" <<'PY'
import json,sys
from pathlib import Path
root=Path(sys.argv[1])
for name in ('status.json','hybrid/report.json','gpu/report.json','comparison.json'):
    p=root/name
    if p.exists():
        data=json.loads(p.read_text())
        keys=('phase','status','completed','reason','setup_s','generation_s','compute_and_buffer_s','current_rebuilds','generation_speedup','compute_and_buffer_speedup')
        print(name,{k:data[k] for k in keys if k in data})
PY
  exit 0
fi
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export WIND3DGS_WORKSPACE="$PWD"
export WARP_CACHE_PATH="${WARP_CACHE_PATH:-$PWD/code/outputs/warp-cache}"
# 별도 vendor 경로에만 설치한다. 기존 venv/runtime에는 쓰지 않는다.
deps=experiments/artifacts/runs/teacher_timestep_search/gpu_resident_dependencies/cudss_0_7_1_6
library="$PWD/$deps/nvidia/cu12/lib/libcudss.so.0"
if [[ ! -f "$library" ]]; then
  "$python_bin" -m pip install --no-deps --target "$deps" nvidia-cudss-cu12==0.7.1.6
fi
PYTHONPATH=code "$python_bin" -u -m wind3dgs.evaluation.teacher_gpu_comparison "$out" --prepare "$config"
# 검토한 동결 C source로 해당 비교 프로세스의 초기 workspace shim을 만든다.
cc -shared -fPIC -O2 -Wall -Wextra -Werror "$out/runtime/native/cudss_workspace.c" -o "$out/runtime/native/libcudss_workspace.so.pending" -ldl -pthread
mv -- "$out/runtime/native/libcudss_workspace.so.pending" "$out/runtime/native/libcudss_workspace.so"
export CUDSS_LIBRARY_PATH="$library"
shim_path="$out/runtime/native/libcudss_workspace.so"
if [[ "$shim_path" != /* ]]; then shim_path="$PWD/$shim_path";fi
export LD_PRELOAD="$shim_path${LD_PRELOAD:+:$LD_PRELOAD}"
if [[ "$mode" == --prepare-only ]]; then printf '%s\n' '비교 입력·동결 코드·GPU 의존성 준비 완료. 시뮬레이션은 실행하지 않았습니다.';exit 0;fi
"$python_bin" - <<'PY'
from pathlib import Path
import os,sys
found=[]
for folder in Path('/proc').iterdir():
    if not folder.name.isdigit() or int(folder.name)==os.getpid():continue
    try:args=(folder/'cmdline').read_bytes().split(b'\0')
    except (OSError,PermissionError):continue
    if b'-m' in args:
        i=args.index(b'-m')+1
        if i<len(args):
            module=args[i].decode(errors='replace')
            if module.startswith('wind3dgs.evaluation.teacher_'):
                found.append((folder.name,module))
if found:
    print('다른 teacher 실행이 남아 있어 비교를 시작하지 않습니다:',found,file=sys.stderr)
    print('직접 중지한 뒤 같은 명령을 실행하세요. 이 스크립트는 기존 실행을 중지하지 않습니다.',file=sys.stderr)
    sys.exit(1)
PY
export PYTHONPATH="$out/runtime/code"
printf '%s\n' '동일 초기 상태에서 하이브리드10프레임 → GPU10프레임 → 독립 검산을 순차 실행합니다.'
printf '로그: %s/comparison.log\n결과: %s/comparison.json\n' "$out" "$out"
if [[ "$mode" == --background ]]; then
  nohup "$python_bin" -u -m wind3dgs.evaluation.teacher_gpu_comparison "$out" >> "$out/comparison.log" 2>&1 < /dev/null &
  printf '백그라운드 PID: %s\n' "$!"
else
  "$python_bin" -u -m wind3dgs.evaluation.teacher_gpu_comparison "$out" 2>&1 | tee -a "$out/comparison.log"
fi
