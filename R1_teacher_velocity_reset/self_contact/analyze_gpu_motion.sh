#!/usr/bin/env bash
# 완료 원본을 CPU에서 분석한다. 새 출력 필수, solver 실행 없음.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code PYTHONDONTWRITEBYTECODE=1 MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/wind3dgs-analysis-mpl}"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
exec .venv/bin/python -m wind3dgs.evaluation.analyze_gpu_contact_recording --action analyze "$@"
