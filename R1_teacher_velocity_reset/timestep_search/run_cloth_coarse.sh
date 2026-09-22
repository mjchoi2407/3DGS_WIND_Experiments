#!/usr/bin/env bash
set -euo pipefail
# 기존 동결 실행은 --legacy를 첫 옵션으로 지정해 접근한다.
if [[ "${1:-}" != --legacy ]]; then
  exec bash "$(dirname -- "${BASH_SOURCE[0]}")/run_cloth_coarse_gpu.sh" "$@"
fi
shift
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
out=experiments/artifacts/runs/teacher_timestep_search/20260913_cloth_coarse_4s_v1
config=experiments/R1_teacher_velocity_reset/timestep_search/cloth_coarse/config.json
mode=run
case_args=()
while (($#)); do
  case "$1" in
    --prepare-only|--status-only|--background|--logs)
      if [[ "$mode" != run ]]; then printf '%s\n' '실행 옵션은 한 번에 하나만 지정하세요.' >&2; exit 2; fi
      mode="$1"; shift ;;
    -h|--help)
      printf '%s\n' '사용법: run_cloth_coarse.sh [--prepare-only|--status-only|--background|--logs] [--case baseline|bend_010|bend_001]'; exit 0 ;;
    --case)
      if (($# < 2)); then printf '%s\n' '--case 뒤에 baseline, bend_010 또는 bend_001이 필요합니다.' >&2; exit 2; fi
      case "$2" in baseline|bend_010|bend_001) case_args=(--case "$2"); shift 2 ;;
        *) printf '%s\n' '알 수 없는 비교 조건입니다.' >&2; exit 2 ;; esac ;;
    *) printf '%s\n' '사용법: run_cloth_coarse.sh [--prepare-only|--status-only|--background|--logs] [--case baseline|bend_010|bend_001]' >&2; exit 2 ;;
  esac
done
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export WARP_CACHE_PATH="${WARP_CACHE_PATH:-$PWD/code/outputs/warp-cache}"
if [[ "$mode" == --logs ]]; then exec tail -n 40 -F "$out/batch.log"; fi
if [[ "$mode" != --status-only ]]; then
  PYTHONPATH=code .venv/bin/python -u -m wind3dgs.evaluation.teacher_cloth_sweep "$out" --prepare "$config"
fi
if [[ "$mode" == --prepare-only ]]; then exit 0; fi
if [[ ! -f "$out/manifest.json" ]]; then printf '%s\n' '먼저 --prepare-only로 비교 묶음을 준비하세요.' >&2; exit 1; fi
export PYTHONPATH="$out/baseline/runtime/code"
if [[ "$mode" == --status-only ]]; then
  exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_cloth_sweep "$out" --status "${case_args[@]}"
fi
if ((${#case_args[@]})); then
  printf '저해상도 천 굽힘 비교: %s의3개 씬, 각각4초 순차 실행.\n' "${case_args[1]}"
else
  printf '%s\n' '저해상도 천 굽힘 비교: 조건별4초, 전체9개 씬 순차 실행.'
fi
printf '%s\n' '로그는 batch.log와 씬별 worker.log에 저장합니다.'
if [[ "$mode" == --background ]]; then
  nohup .venv/bin/python -u -m wind3dgs.evaluation.teacher_cloth_sweep "$out" "${case_args[@]}" >> "$out/batch.log" 2>&1 < /dev/null &
  printf '백그라운드 controller PID: %s\n상태 확인: 같은 스크립트 --status-only\n로그 보기: 같은 스크립트 --logs\n' "$!"
else
  .venv/bin/python -u -m wind3dgs.evaluation.teacher_cloth_sweep "$out" "${case_args[@]}" 2>&1 | tee -a "$out/batch.log"
fi
