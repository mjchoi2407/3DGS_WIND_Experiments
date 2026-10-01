#!/usr/bin/env bash
# 기존·시간 평활·넓은 국소 바람의 완료 결과만 동기 재생한다.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
wind_field_python="${WIND3DGS_PYTHON:-$PWD/.venv/bin/python}"
exec "$wind_field_python" -u -m wind3dgs.evaluation.view_gpu_wind_field "$@"
