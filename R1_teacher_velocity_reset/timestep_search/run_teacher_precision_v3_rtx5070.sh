#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_precision_v3 --gpu rtx5070 --out experiments/artifacts/runs/teacher_precision_v3/rtx5070_v3 "$@"
