#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
out=experiments/artifacts/runs/teacher_timestep_search/20260912_triangle_regular_01s_v1
case "${1:-}" in
  --status-only)
    PYTHONPATH="$out/runtime/code" .venv/bin/python -m wind3dgs.evaluation.teacher_three_scene_run "$out" --status
    ;;
  "")
    printf '%s\n' '삼각 깃발 단기 검증: 목표 0.1초·6프레임. 동결 실행기의 /10초 표시는 공통 출력 문구입니다.'
    PYTHONPATH="$out/runtime/code" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -u -m wind3dgs.evaluation.teacher_three_scene_run "$out"
    ;;
  *) printf '%s\n' '사용법: run_triangle_regular_check.sh [--status-only]' >&2; exit 2 ;;
esac
