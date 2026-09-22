#!/usr/bin/env bash
set -euo pipefail
script=experiments/R1_teacher_velocity_reset/timestep_search/gpu_resident/audit_run.py
python_bin="${WIND3DGS_PYTHON:-.venv/bin/python}"
log=experiments/artifacts/runs/teacher_timestep_search/gpu_audit_launcher.log
if [[ "${1:-}" == --logs ]]; then exec tail -n 60 -F "$log"; fi
if [[ "${1:-}" == --background ]]; then
  shift
  mkdir -p -- "$(dirname -- "$log")"
  nohup "$python_bin" -u "$script" "$@" >> "$log" 2>&1 < /dev/null &
  printf 'GPU 검산 PID: %s\n로그: %s\n' "$!" "$log"
else
  "$python_bin" -u "$script" "$@"
fi
