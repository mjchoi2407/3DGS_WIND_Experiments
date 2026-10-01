#!/usr/bin/env bash
# 기본은 상태 확인. prepare는 입력 준비만, run에서만 GPU 계산.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
exec .venv/bin/python -m wind3dgs.evaluation.teacher_gpu_damping_sample "$@"
