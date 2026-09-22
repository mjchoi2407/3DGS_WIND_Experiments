#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
out=experiments/artifacts/runs/teacher_timestep_search/20260912_three_scenes_10s_v4
case "${1:-}" in
  --prepare-only)
    PYTHONPATH=code .venv/bin/python -m wind3dgs.evaluation.teacher_three_scene_run "$out" --prepare --unlimited-all --rebuild-every 64 --resume-from experiments/artifacts/runs/teacher_timestep_search/20260912_three_scenes_10s_v3
    ;;
  --status-only)
    PYTHONPATH="$out/runtime/code" .venv/bin/python -m wind3dgs.evaluation.teacher_three_scene_run "$out" --status
    ;;
  "")
    PYTHONPATH="$out/runtime/code" OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 .venv/bin/python -u -m wind3dgs.evaluation.teacher_three_scene_run "$out"
    ;;
  *) printf '%s\n' '사용법: run_three_scenes.sh [--prepare-only|--status-only]' >&2; exit 2 ;;
esac
