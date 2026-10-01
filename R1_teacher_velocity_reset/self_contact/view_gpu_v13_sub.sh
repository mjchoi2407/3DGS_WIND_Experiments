#!/usr/bin/env bash
# RTX5070 완료 v13: 시작 굽힘부터1/4/5초 전체 궤적 재생.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
exec bash experiments/R1_teacher_velocity_reset/self_contact/view_gpu_v13.sh \
  --run experiments/artifacts/runs/sub_pc/20260928T043613Z-b306cdad658642d089bb9b2330f8fdae/simulation "$@"
