#!/usr/bin/env bash
# 4배·rest 우선/current 전환. 10초 본 실행 전체에 새4시간 한도. 이전 실행/개발 비용은 차감하지 않는다.
set -euo pipefail
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec bash "$WORKSPACE_DIR/code/scripts/run_teacher_timestep_search.sh" \
  --output experiments/artifacts/runs/teacher_timestep_search/20260911_adaptive4_segments_v2 \
  --precision --target-substeps 64 --linear-preconditioner current \
  --preconditioner-rebuild-every 4 --adaptive-preconditioner-iterations 32 \
  --linear-restart 240 --linear-cycles 3 --first-candidate-only \
  --segment-seconds 2.5 --pause-after-segment \
  --budget-hours 4 --trial-timeout 14400 "$@"
