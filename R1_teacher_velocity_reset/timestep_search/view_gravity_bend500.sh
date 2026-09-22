#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
phase="${1:-wind}"
if (($#)); then shift; fi
exec bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh "$phase" \
  --out experiments/artifacts/runs/teacher_timestep_search/gravity_wrinkles_flag_bend500_v1 "$@"
