#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_precision_v3 --gpu gtx1080ti --out experiments/artifacts/runs/teacher_precision_v3/gtx1080ti_v3 "$@"
