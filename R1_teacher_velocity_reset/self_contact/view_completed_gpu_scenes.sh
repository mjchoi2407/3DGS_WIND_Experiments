#!/usr/bin/env bash
# 완료된 v11 손수건·삼각형 preload→wind 저장 프레임을 나란히 재생한다.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export WARP_CACHE_PATH="${WARP_CACHE_PATH:-$PWD/code/outputs/warp-cache}"
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
exec .venv/bin/python -m wind3dgs.evaluation.view_gpu_contact_recording "$@"
