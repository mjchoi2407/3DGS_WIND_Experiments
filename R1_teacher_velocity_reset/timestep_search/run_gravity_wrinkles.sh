#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export WARP_CACHE_PATH="${WARP_CACHE_PATH:-$PWD/code/outputs/warp-cache}"
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_gravity_wrinkles "$@"
