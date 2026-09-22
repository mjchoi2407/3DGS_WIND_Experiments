#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
export PYTHONPATH=code
if [[ "${1:-}" == "--profile" ]]; then
    shift
    exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_precision_profile "$@"
fi
exec .venv/bin/python -u -m wind3dgs.evaluation.teacher_newmark_dt_suite --mode gauss_retry "$@"
