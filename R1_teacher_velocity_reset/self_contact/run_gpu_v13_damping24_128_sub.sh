#!/usr/bin/env bash
# 서브컴 로컬 Python + 읽기 전용 공유 입력 + 전용 결과 폴더.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
exec "${WIND3DGS_PYTHON:-$HOME/wind3dgs-worker/venv/bin/python}" -u -m wind3dgs.evaluation.teacher_gpu_damped_trajectory \
  --substeps 128 \
  --stage-from "$PWD/experiments/artifacts/runs/p3_self_contact/rectangle_gpu_drape_v13_damping24_steps128_01" \
  --out /mnt/wind3dgs-sub-results/damping24_steps128_01 "$@"
