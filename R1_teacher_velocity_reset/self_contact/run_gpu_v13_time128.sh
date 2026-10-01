#!/usr/bin/env bash
# 완료 서브 v13과 같은 동결 runtime; 기본은 상태 확인, 명시적 run만 GPU 계산.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_gpu_time_refinement "$@"
