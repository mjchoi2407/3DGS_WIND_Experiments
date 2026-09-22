#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export WARP_CACHE_PATH="${WARP_CACHE_PATH:-$PWD/code/outputs/warp-cache}"
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
printf '%s\n' '완료된 직사각형·손수건 저장 결과 재생. Space: 재생/정지, 왼쪽 드래그: 회전, 휠: 확대. 처음에는 정지 상태입니다.'
exec .venv/bin/python -m wind3dgs.evaluation.view_shell_recording "$@"
