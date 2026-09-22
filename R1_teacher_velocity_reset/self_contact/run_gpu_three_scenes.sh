#!/usr/bin/env bash
# 기본은 GPU 실행 묶음 준비. --action run은 세 씬을 GPU에서 순차 실행한다.
# 사용자 직접 실행 전용v10. 시간 보정과 유한한 code2의 GPU dt/2 복구를 사용한다.
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
# CUDA는 큰 가상 주소 공간을 예약하므로 CPU 실행기의 ulimit -v를 적용하지 않는다.
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_gpu_contact_scene_suite \
  --out experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v10 "$@"
