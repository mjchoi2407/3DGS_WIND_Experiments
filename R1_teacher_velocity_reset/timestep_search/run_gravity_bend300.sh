#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
exec bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_wrinkles.sh \
  --out experiments/artifacts/runs/teacher_timestep_search/gravity_wrinkles_flag_bend300_v1 \
  --bending-ratio 0.0033333333333333335 "$@"
