#!/usr/bin/env bash
# 메인 GTX1080Ti: 막5ms 고정·굽힘1/5ms·8→10초. 기본status.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
bend_python="${WIND3DGS_PYTHON:-$PWD/.venv/bin/python}"
exec "$bend_python" -u -m wind3dgs.evaluation.teacher_gpu_bending_damping "$@"
