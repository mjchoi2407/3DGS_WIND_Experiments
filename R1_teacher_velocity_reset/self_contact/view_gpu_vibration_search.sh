#!/usr/bin/env bash
# 선정한 후보와 원본 기준을 공통 시간으로 비교한다.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
vibration_python="${WIND3DGS_PYTHON:-$PWD/.venv/bin/python}"
exec "$vibration_python" -u -m wind3dgs.evaluation.view_gpu_vibration_search "$@"
