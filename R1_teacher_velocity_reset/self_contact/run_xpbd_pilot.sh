#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
pilot_python="${WIND3DGS_PYTHON:-$PWD/.venv/bin/python}"
exec "$pilot_python" -u -m wind3dgs.evaluation.teacher_xpbd_pilot "$@"
