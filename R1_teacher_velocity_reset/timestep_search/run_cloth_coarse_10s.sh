#!/usr/bin/env bash
set -euo pipefail
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/run_cloth_coarse_gpu.sh" \
  --out experiments/artifacts/runs/teacher_timestep_search/20260913_cloth_coarse_10s_visual_v1 \
  --config experiments/R1_teacher_velocity_reset/timestep_search/cloth_coarse/gpu_10s_visual_config.json "$@"
