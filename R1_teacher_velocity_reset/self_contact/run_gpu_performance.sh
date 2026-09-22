#!/usr/bin/env bash
# 다른 GPU 작업을 종료한 후 --gpu-idle-confirmed를 명시한다. 본 시뮬레이션은 실행하지 않는다.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
contact_run=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v5
export PYTHONPATH="$contact_run/runtime"
export CUDSS_LIBRARY_PATH="$contact_run/native/libcudss.so.0"
export LD_PRELOAD="$contact_run/native/libcudss_workspace.so"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
export WARP_CACHE_PATH=/tmp/wind3dgs-gpu-contact-cache
exec timeout --kill-after=15 900 .venv/bin/python -u -m wind3dgs.evaluation.p3_gpu_contact_performance \
  --scenes "$contact_run" \
  --out experiments/artifacts/runs/p3_self_contact/performance_idle_v5 "$@"
