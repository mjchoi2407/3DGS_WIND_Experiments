#!/usr/bin/env bash
# 서브 컴 완료 v13의 CPU 분석. 매번 새 출력 경로를 사용한다.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
analysis_stamp=$(date -u +%Y%m%dT%H%M%S%NZ)
exec bash experiments/R1_teacher_velocity_reset/self_contact/analyze_gpu_motion.sh \
  --run experiments/artifacts/runs/sub_pc/20260928T043613Z-b306cdad658642d089bb9b2330f8fdae/simulation \
  --out "experiments/artifacts/runs/p3_self_contact/motion_analysis/v13_sub_${analysis_stamp}" "$@"
