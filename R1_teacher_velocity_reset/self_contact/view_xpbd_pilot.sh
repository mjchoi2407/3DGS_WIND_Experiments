#!/usr/bin/env bash
set -euo pipefail
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/run_xpbd_pilot.sh" --action view --out experiments/artifacts/runs/xpbd_small_steps/rectangle_xpbd_small_20260930_01_refine64_01 "$@"
