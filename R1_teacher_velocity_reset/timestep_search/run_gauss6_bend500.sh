#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
shape="${1:?씬 이름이 필요합니다}"; shift
case "$shape" in reference_rectangle|triangular_flag|handkerchief) ;; *) echo '지원하지 않는 씬' >&2; exit 2;; esac
base=experiments/artifacts/runs/teacher_timestep_search
args=()
for arg in "$@"; do
  if [[ "$arg" == --sub-pc ]]; then base=experiments/artifacts/runs/sub_pc; else args+=("$arg"); fi
done
exec bash experiments/R1_teacher_velocity_reset/timestep_search/run_gravity_wrinkles.sh \
  --solver-backend gauss6 --bending-ratio 0.002 --shape "$shape" \
  --out "$base/gauss6_split8_bend500_${shape}_v1" "${args[@]}"
