#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code

out="experiments/artifacts/runs/teacher_precision_v3/extended32_frame_breakdown_$(date +%Y%m%dT%H%M%S)"

# 기본 1회씩만 실행한다. 표시 190/194/200의 각 프레임 전체가 수 분 걸리며,
# 각 worker는 같은 시작 상태에서 M2와 확장 FP32를 독립 실행한다.
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_extended_precision_probe \
  --profile --full-frame --pairs 1 --out "$out" "$@"
