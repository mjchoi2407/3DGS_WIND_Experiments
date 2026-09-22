#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
out=experiments/artifacts/runs/teacher_timestep_search/20260913_cloth_coarse_4s_gpu_v6
config=experiments/R1_teacher_velocity_reset/timestep_search/cloth_coarse/gpu_config.json
mode=run
args=()
while (($#)); do
  case "$1" in
    --prepare-only|--status-only|--background|--logs)
      [[ "$mode" == run ]] || { printf '%s\n' '실행 모드는 하나만 지정하세요.' >&2; exit 2; }
      mode="$1"; shift ;;
    --out|--config|--case|--shape)
      (($# >= 2)) || { printf '%s\n' '옵션 값이 필요합니다.' >&2; exit 2; }
      case "$1" in
        --out) out="$2" ;; --config) config="$2" ;;
        *) args+=("$1" "$2") ;;
      esac
      shift 2 ;;
    -h|--help)
      printf '%s\n' '사용법: run_cloth_coarse.sh [--prepare-only|--status-only|--background|--logs] [--case baseline|bend_010|bend_001] [--shape reference_rectangle|triangular_flag|handkerchief] [--out 경로] [--config JSON]' '기존 하이브리드 실행: run_cloth_coarse.sh --legacy [옵션]'; exit 0 ;;
    *) printf '알 수 없는 옵션: %s\n' "$1" >&2; exit 2 ;;
  esac
done
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export WARP_CACHE_PATH="${WARP_CACHE_PATH:-$PWD/code/outputs/warp-cache}"
if [[ "$mode" == --logs ]]; then exec tail -n 40 -F "$out/batch.log"; fi
if [[ "$mode" != --status-only ]]; then
  PYTHONPATH=code .venv/bin/python -u -m wind3dgs.evaluation.teacher_cloth_gpu_sweep "$out" --prepare "$config"
fi
[[ "$mode" != --prepare-only ]] || exit 0
[[ -f "$out/manifest.json" ]] || { printf '%s\n' '먼저 --prepare-only로 준비하세요.' >&2; exit 1; }
export PYTHONPATH="$out/baseline/runtime/code"
if [[ "$mode" == --status-only ]]; then
  exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_cloth_gpu_sweep "$out" --status "${args[@]}"
fi
printf '%s\n' 'GPU 계산·독립 검산: 선택한 설정의 씬을 순차 실행. 매 프레임 시간 출력·저장 간격 기본2초.' '상세 진행은 씬별 worker.log, 전체 상태는 batch.log에 저장합니다.'
if [[ "$mode" == --background ]]; then
  nohup .venv/bin/python -u -m wind3dgs.evaluation.teacher_cloth_gpu_sweep "$out" "${args[@]}" >> "$out/batch.log" 2>&1 < /dev/null &
  printf 'controller PID: %s\n' "$!"
else
  .venv/bin/python -u -m wind3dgs.evaluation.teacher_cloth_gpu_sweep "$out" "${args[@]}" 2>&1 | tee -a "$out/batch.log"
fi
