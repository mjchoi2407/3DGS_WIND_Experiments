#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
exec bash experiments/R1_teacher_velocity_reset/timestep_search/run_gauss6_bend500.sh handkerchief "$@"
