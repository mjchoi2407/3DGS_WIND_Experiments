#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
script=experiments/R1_teacher_velocity_reset/timestep_search/gpu_resident/parallel_compare.py
python_bin="${WIND3DGS_PYTHON:-.venv/bin/python}"
log=experiments/artifacts/runs/teacher_timestep_search/gpu_current_first_launcher.log
if [[ "${1:-}" == --logs ]]; then exec tail -n 60 -F "$log"; fi
if [[ "${1:-}" == --background ]]; then
  shift
  mkdir -p -- "$(dirname -- "$log")"
  nohup "$python_bin" -u "$script" --method current-first --out experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_current_first_v1 "$@" >> "$log" 2>&1 < /dev/null &
  printf 'current 우선 비교 PID: %s\n로그: %s\n' "$!" "$log"
else
  "$python_bin" -u "$script" --method current-first --out experiments/artifacts/runs/teacher_timestep_search/20260913_gpu_current_first_v1 "$@"
fi
