#!/usr/bin/env bash
# 완료된 v13 1/4/5초 저장 궤적만 재생한다.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export WARP_CACHE_PATH="${WARP_CACHE_PATH:-$PWD/code/outputs/warp-cache}"
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
exec .venv/bin/python -m wind3dgs.evaluation.view_gpu_contact_recording \
  --run experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_drape_v13 \
  --phase trajectory --shape all "$@"
