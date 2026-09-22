#!/usr/bin/env bash
# 4배(64분할), 현재 보조 행렬4회 재사용. 각2.5초에서 판정 대기.
set -euo pipefail
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec bash "$WORKSPACE_DIR/code/scripts/run_teacher_timestep_search.sh" \
  --output experiments/artifacts/runs/teacher_timestep_search/20260911_acceleration4_segments_v1 \
  --precision --target-substeps 64 --linear-preconditioner current \
  --preconditioner-rebuild-every 4 --linear-restart 240 --linear-cycles 3 \
  --first-candidate-only --segment-seconds 2.5 --pause-after-segment \
  --budget-hours 2.2216666666666667 --trial-timeout 7998 "$@"
