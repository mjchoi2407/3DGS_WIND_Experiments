#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
version=gpu
if [[ "${1:-}" == --legacy ]]; then version=legacy; shift; fi
variant="${1:-baseline}"
case "$variant" in
  baseline|bend_010|bend_001) if (($#)); then shift; fi ;;
  *) printf '%s\n' '사용법: view_cloth_coarse.sh [baseline|bend_010|bend_001] [--shape reference_rectangle|triangular_flag|handkerchief|both] [뷰어 옵션]' >&2; exit 2 ;;
esac
out=experiments/artifacts/runs/teacher_timestep_search/20260913_cloth_coarse_4s_gpu_v6
if [[ "$version" == legacy ]]; then out=experiments/artifacts/runs/teacher_timestep_search/20260913_cloth_coarse_4s_v1; fi
export PYTHONPATH="$out/$variant/runtime/code"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export WARP_CACHE_PATH="${WARP_CACHE_PATH:-$PWD/code/outputs/warp-cache}"
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
printf '%s\n' "$variant 완료 결과 재생. 기본은 직사각형·손수건이며 삼각 깃발은 --shape triangular_flag로 선택합니다."
exec .venv/bin/python -m wind3dgs.evaluation.view_shell_recording \
  --run "$out/$variant" --cache "$out/playback/$variant" "$@"
