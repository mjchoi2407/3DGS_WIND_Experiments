#!/usr/bin/env bash
# 기본 동작은 준비만. 사용자가 --action run을 명시하면 본 계산.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_gpu_contact_drape_suite "$@"
