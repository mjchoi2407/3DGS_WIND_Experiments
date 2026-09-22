#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code

out="experiments/artifacts/runs/teacher_precision_v3/gauss_precision_preload_$(date +%Y%m%dT%H%M%S)"
input="experiments/artifacts/runs/teacher_timestep_search/gauss_scaling_trial_v1/inputs/preload/input.npz"
reference="experiments/artifacts/runs/teacher_timestep_search/gpu_gtx1080ti_auto_bend500_v1/reference_rectangle/preload/reference_rectangle/frame_timings.jsonl"

# 평면 rest 상태에서 중력 ramp 첫 held가 적용되는 표시 frame 1 한 개만 비교한다.
# GTX 1080 Ti 기본 block 설정이며, RTX 5070은 끝에 --blocks 32 32 256을 지정한다.
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_gauss_precision_frame_probe \
  --preload-input "$input" --reference-timing "$reference" \
  --pairs 1 --blocks 256 256 256 --out "$out" "$@"
