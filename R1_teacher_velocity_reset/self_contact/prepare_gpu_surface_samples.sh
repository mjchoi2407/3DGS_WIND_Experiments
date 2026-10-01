#!/usr/bin/env bash
# 동결 입력의 공통512점 map만 준비한다. 본 실행·결과 변경 없음.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
exec .venv/bin/python -m wind3dgs.evaluation.analyze_gpu_contact_recording --action map "$@"
