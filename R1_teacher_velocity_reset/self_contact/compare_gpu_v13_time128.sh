#!/usr/bin/env bash
# 서브 v13 기본64 결과와 새 사각형128 결과의 CPU 시간 민감도 비교.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
exec bash experiments/R1_teacher_velocity_reset/self_contact/compare_gpu_v13_sub.sh \
  --reference experiments/artifacts/runs/p3_self_contact/rectangle_gpu_drape_v13_time128 \
  --shape reference_rectangle "$@"
