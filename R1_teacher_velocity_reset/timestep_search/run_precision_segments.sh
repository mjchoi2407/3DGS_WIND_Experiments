#!/usr/bin/env bash
# 60 Hz 바람·1분할(256배 고정 목표), 2.5초씩 검산 후 이어가기.
# v1/v2/v3의 사용 시간을 차감하여 원래4시간 중7998초를 남긴다.
set -euo pipefail
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
exec bash "$WORKSPACE_DIR/code/scripts/run_teacher_timestep_search.sh" \
  --output experiments/artifacts/runs/teacher_timestep_search/20260911_target256_segments_v2 \
  --precision --target-substeps 1 --linear-preconditioner current --linear-restart 240 --linear-cycles 3 --first-candidate-only --segment-seconds 2.5 \
  --budget-hours 2.2216666666666667 --trial-timeout 7998 "$@"
