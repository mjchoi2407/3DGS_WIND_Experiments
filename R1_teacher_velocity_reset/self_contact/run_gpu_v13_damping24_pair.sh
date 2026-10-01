#!/usr/bin/env bash
# 한 PC의 cuda:0에서64→128 순차 실행. 기본은 status.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
if [[ "$PWD" == /mnt/wind3dgs || "$PWD" == /mnt/wind3dgs/* ]]; then
  pair_python="${WIND3DGS_PYTHON:-$HOME/wind3dgs-worker/venv/bin/python}"
  pair_output=/mnt/wind3dgs-sub-results/damping24_single_pc_01
else
  pair_python="${WIND3DGS_PYTHON:-$PWD/.venv/bin/python}"
  pair_output=experiments/artifacts/runs/p3_self_contact/rectangle_gpu_drape_v13_damping24_single_pc_01
fi
exec "$pair_python" -u -m wind3dgs.evaluation.teacher_gpu_damping24_pair --out "$pair_output" "$@"
