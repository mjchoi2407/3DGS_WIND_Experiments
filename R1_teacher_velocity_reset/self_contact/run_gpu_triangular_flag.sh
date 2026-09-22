#!/usr/bin/env bash
set -euo pipefail
exec bash "$(dirname "${BASH_SOURCE[0]}")/run_gpu_three_scenes.sh" --action run "$@" --shape triangular_flag
