#!/usr/bin/env bash
# 완료 RTX5070 감쇠24 사각형: 기본64, 전체5초(wind 시작)에서 일시정지.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
view_steps=64
view_args=()
while (($#)); do
  case "$1" in
    --steps)
      if (($# < 2)); then echo '--steps에는64 또는128이 필요합니다' >&2; exit 2; fi
      view_steps="$2"; shift 2 ;;
    --steps=*) view_steps="${1#*=}"; shift ;;
    -h|--help)
      echo '사용: bash view_gpu_v13_damping24.sh [--steps 64|128] [--time 초] [--prepare-only]'
      echo '기본64·전체5초에서 일시정지. Space 재생, Time 슬라이더0–10초, Playback speed 속도 조절.'
      exit 0 ;;
    *) view_args+=("$1"); shift ;;
  esac
done
case "$view_steps" in 64|128) ;; *) echo '--steps는64 또는128이어야 합니다' >&2; exit 2 ;; esac
export PYTHONPATH="$PWD/code" PYTHONDONTWRITEBYTECODE=1
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
view_cache_args=()
if [[ "$PWD" == /mnt/wind3dgs || "$PWD" == /mnt/wind3dgs/* ]]; then
  view_python="${WIND3DGS_PYTHON:-$HOME/wind3dgs-worker/venv/bin/python}"
  view_cache_args=(--cache "$HOME/wind3dgs-worker/cache/damping24_20260929_steps${view_steps}")
else
  view_python="${WIND3DGS_PYTHON:-$PWD/.venv/bin/python}"
fi
view_run="experiments/artifacts/runs/sub_pc/20260929T002107Z-65221d3a61d34d0f93b4d01006eb5602/simulation/steps${view_steps}"
echo "감쇠24·기본${view_steps}: 원본10초 궤적, 기본 재생 시작5초"
exec "$view_python" -m wind3dgs.evaluation.view_gpu_contact_recording \
  --run "$view_run" --shape reference_rectangle --phase trajectory --time 5 \
  "${view_cache_args[@]}" "${view_args[@]}"
