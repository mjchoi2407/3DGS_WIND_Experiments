#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_dual_gpu_followup "$@"
