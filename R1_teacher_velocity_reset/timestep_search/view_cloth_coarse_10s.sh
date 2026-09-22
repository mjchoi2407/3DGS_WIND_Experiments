#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
if [[ "${1:-}" == --help || "${1:-}" == -h ]]; then
  printf '%s\n' '사용법: bash experiments/R1_teacher_velocity_reset/timestep_search/view_cloth_coarse_10s.sh [baseline|bend_010|bend_001] [--shape reference_rectangle|triangular_flag|handkerchief|both] [--time 초] [--prepare-only]' '서브컴에서 완료한 10초 결과를 재생합니다. 기본은 baseline의 직사각형·손수건입니다.' '첫 실행은 저장 상태의 해시 검증과 표시 캐시 생성에 시간이 걸립니다. 이후에는 캐시를 재사용합니다.'
  exit 0
fi
variant="${1:-baseline}"
case "$variant" in baseline|bend_010|bend_001) if (($#)); then shift; fi ;; *) printf '%s\n' '굽힘 조건은 baseline, bend_010, bend_001 중 선택하세요. 사용법: --help' >&2; exit 2 ;; esac
out=experiments/artifacts/runs/sub_pc/20260912T223433Z-aca6fc4223714a02a9fe8afe7f4edeef
export PYTHONPATH="$out/$variant/runtime/code"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export WARP_CACHE_PATH="${WARP_CACHE_PATH:-$PWD/code/outputs/warp-cache}"
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
printf '%s\n' '시각 확인 전용: 기하 경고가 있어도 계산한 결과입니다. 엄격 검산 통과 결과가 아닙니다.'
exec .venv/bin/python -m wind3dgs.evaluation.view_shell_recording --run "$out/$variant" --cache "$out/playback/$variant" "$@"
