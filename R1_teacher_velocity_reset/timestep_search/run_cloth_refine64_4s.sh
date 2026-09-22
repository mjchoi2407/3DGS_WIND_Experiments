#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
out=experiments/artifacts/runs/teacher_timestep_search/20260913_cloth_three_fp64_4s_v2
mode=run
args=()
while (($#)); do
  case "$1" in
    --prepare-only|--status-only|--compare-only|--background|--logs)
      [[ "$mode" == run ]] || { printf '%s\n' '실행 모드는 하나만 지정하세요.' >&2; exit 2; }
      mode="$1"; shift ;;
    --out|--source|--shape|--frames)
      (($# >= 2)) || { printf '%s\n' '옵션 값이 필요합니다.' >&2; exit 2; }
      if [[ "$1" == --out ]]; then out="$2"; else args+=("$1" "$2"); fi
      shift 2 ;;
    -h|--help)
      printf '%s\n' '사용법: run_cloth_refine64_4s.sh [--prepare-only|--status-only|--compare-only|--background|--logs] [--shape reference_rectangle|triangular_flag|handkerchief] [--out 경로]' \
        '기본: FP64 hi/lo 원본 재사용 + pure FP64 기존 풀이 + FP64 보정. 두 풀이×세 메시를 각각4초 순차 실행·자동 비교.' \
        '유한 정확도 초과는 기록하며 계속, 비유한/계산 불능은 종료. 학습 적격 데이터가 아닙니다.' \
        '기존4초 목표 실행은 조기 중단됐으므로 속도비는 공통 정상 구간에만 제공합니다.'
      exit 0 ;;
    *) printf '알 수 없는 옵션: %s\n' "$1" >&2; exit 2 ;;
  esac
done
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
export WARP_CACHE_PATH="${WARP_CACHE_PATH:-$PWD/code/outputs/warp-cache}"
if [[ "$mode" == --logs ]]; then exec tail -n 40 -F "$out/batch.log"; fi
module=wind3dgs.evaluation.teacher_cloth_fp64_suite
if [[ "$mode" != --status-only && "$mode" != --compare-only ]]; then
  PYTHONPATH=code .venv/bin/python -u -m "$module" --out "$out" --prepare-only "${args[@]}"
fi
[[ "$mode" != --prepare-only ]] || exit 0
[[ -f "$out/manifest.json" ]] || { printf '%s\n' '먼저 --prepare-only로 준비하세요.' >&2; exit 1; }
export PYTHONPATH="$out/refine64/bend_001/runtime/code"
if [[ "$mode" == --status-only || "$mode" == --compare-only ]]; then
  exec .venv/bin/python -u -m "$module" --out "$out" "$mode" "${args[@]}"
fi
if [[ "$mode" == --background ]]; then
  nohup .venv/bin/python -u -m "$module" --out "$out" "${args[@]}" >> "$out/batch.log" 2>&1 < /dev/null &
  printf 'controller PID: %s\n' "$!"
else
  .venv/bin/python -u -m "$module" --out "$out" "${args[@]}" 2>&1 | tee -a "$out/batch.log"
fi
