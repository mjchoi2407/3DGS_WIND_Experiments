#!/usr/bin/env bash
# 신규 묶음 준비/개별 검산/실행. 기존 결과·로그가 있으면 덮어쓰지 않는다.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
wind_field_python="${WIND3DGS_PYTHON:-$PWD/.venv/bin/python}"
exec "$wind_field_python" -u -m wind3dgs.evaluation.teacher_gpu_wind_field "$@"
