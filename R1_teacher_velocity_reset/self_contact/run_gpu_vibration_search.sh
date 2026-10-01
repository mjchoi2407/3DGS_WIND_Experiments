#!/usr/bin/env bash
# P3 잔진동·비용 탐색. 기본값은 상태 조회, 기존 결과 덮어쓰기 없음.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
vibration_python="${WIND3DGS_PYTHON:-$PWD/.venv/bin/python}"
exec "$vibration_python" -u -m wind3dgs.evaluation.teacher_gpu_vibration_search "$@"
