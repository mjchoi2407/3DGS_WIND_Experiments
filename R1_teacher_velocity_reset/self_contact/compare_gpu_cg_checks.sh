#!/usr/bin/env bash
# 완료 원본 두 개의 CPU 비교. 입력 생성/시뮬레이션/자동 시각 승인 없음.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
export MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/wind3dgs-analysis-mpl}"
exec .venv/bin/python -m wind3dgs.evaluation.compare_gpu_cg_checks "$@"
