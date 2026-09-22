#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code
out="experiments/artifacts/runs/teacher_precision_v3/extended32_breakdown_$(date +%Y%m%dT%H%M%S)"
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_extended_precision_probe --profile --out "$out" "$@"
