#!/usr/bin/env bash
# 새 --out이 필요하다. 세 씬 prepare로 검증·복사한 native library만 재사용한다.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v5/runtime
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
export WARP_CACHE_PATH=/tmp/wind3dgs-gpu-contact-cache
export CUDSS_LIBRARY_PATH=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v5/native/libcudss.so.0
export LD_PRELOAD=experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v5/native/libcudss_workspace.so
exec .venv/bin/python -u -m wind3dgs.evaluation.p3_gpu_contact_validation "$@"
