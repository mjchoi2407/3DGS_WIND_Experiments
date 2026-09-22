#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
exec .venv/bin/python code/scripts/view_newmark_dt.py --mode gauss_retry "$@"
