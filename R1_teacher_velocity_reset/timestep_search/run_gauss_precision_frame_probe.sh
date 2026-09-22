#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code

out="experiments/artifacts/runs/teacher_precision_v3/gauss_precision_frame_$(date +%Y%m%dT%H%M%S)"

# 표시 frame 190/194/200을 같은 시작 상태에서 순차 비교한다.
# GTX 1080 Ti 기본 block 설정이다. RTX 5070에서는 끝에
#   --blocks 32 32 256
# 을 붙여 별도 결과 폴더에서 실행한다.
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_gauss_precision_frame_probe \
  --pairs 1 --blocks 256 256 256 --out "$out" "$@"
