#!/usr/bin/env bash
# 사용자 확인 후에만 제한 비교를 실행한다. 본 시뮬레이션은 실행하지 않는다.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
contact_run=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v5
export PYTHONPATH="$contact_run/runtime"
export CUDSS_LIBRARY_PATH="$contact_run/native/libcudss.so.0"
export LD_PRELOAD="$contact_run/native/libcudss_workspace.so"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
exec timeout --kill-after=15 600 .venv/bin/python -u -m wind3dgs.evaluation.p3_gpu_contact_broadphase_benchmark \
  --scenes "$contact_run" --compare --repeats 3 \
  --out experiments/artifacts/runs/p3_self_contact/broadphase_v5_recheck "$@"
