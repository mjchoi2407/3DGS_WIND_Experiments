#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
out=experiments/artifacts/runs/teacher_timestep_search/20260912_triangle_regular_10s_v1
case "${1:-}" in
  --prepare-only)
    PYTHONPATH=experiments/artifacts/runs/teacher_timestep_search/20260912_triangle_regular_01s_v1/runtime/code .venv/bin/python experiments/R1_teacher_velocity_reset/timestep_search/evidence/triangle_failure_20260912/prepare_regular_10s.py
    ;;
  --status-only)
    PYTHONPATH="$out/runtime/code" .venv/bin/python -m wind3dgs.evaluation.teacher_three_scene_run "$out" --status
    ;;
  "")
    printf '%s\n' '고른 삼각 깃발10초 실행: 초기 상태부터600프레임, 시간 한도 없음. 진행 상태는 약15초마다 표시됩니다.'
    PYTHONPATH="$out/runtime/code" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -u -m wind3dgs.evaluation.teacher_three_scene_run "$out"
    ;;
  *) printf '%s\n' '사용법: run_triangle_regular_10s.sh [--prepare-only|--status-only]' >&2; exit 2 ;;
esac
