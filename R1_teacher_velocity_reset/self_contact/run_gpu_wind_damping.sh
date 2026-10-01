#!/usr/bin/env bash
# 기본status. 새 계산8→16, 기존24는 재사용. 서브RTX5070에서run.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 TBB_NUM_THREADS=1
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
wind_input=experiments/artifacts/runs/p3_self_contact/rectangle_wind_damping8_16_from24_01
wind_args=()
if [[ "$PWD" == /mnt/wind3dgs || "$PWD" == /mnt/wind3dgs/* ]]; then
  wind_python="${WIND3DGS_PYTHON:-$HOME/wind3dgs-worker/venv/bin/python}"
  wind_out=/mnt/wind3dgs-sub-results/wind_damping8_16_from24_01
  wind_args=(--stage-from "$PWD/$wind_input" --cache "$HOME/wind3dgs-worker/cache/wind_damping8_16_24")
else
  wind_python="${WIND3DGS_PYTHON:-$PWD/.venv/bin/python}"
  wind_out="$wind_input"
  if [[ -f experiments/artifacts/runs/sub_pc/wind_damping8_16_from24_01/suite.json ]]; then
    wind_out=experiments/artifacts/runs/sub_pc/wind_damping8_16_from24_01
  fi
fi
exec "$wind_python" -u -m wind3dgs.evaluation.teacher_gpu_wind_damping --out "$wind_out" "${wind_args[@]}" "$@"
