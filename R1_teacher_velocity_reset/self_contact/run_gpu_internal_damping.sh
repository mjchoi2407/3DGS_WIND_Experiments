#!/usr/bin/env bash
# 메인 GTX1080Ti 전용: 내부 감쇠1ms/5ms. 기본status, run만GPU계산.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
internal_python="${WIND3DGS_PYTHON:-$PWD/.venv/bin/python}"
exec "$internal_python" -u -m wind3dgs.evaluation.teacher_gpu_internal_damping "$@"
