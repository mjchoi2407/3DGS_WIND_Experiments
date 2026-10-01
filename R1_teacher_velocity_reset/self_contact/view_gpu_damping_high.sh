#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
exec bash experiments/R1_teacher_velocity_reset/self_contact/run_gpu_damping_sample.sh --profile high --out experiments/artifacts/runs/p3_self_contact/damping_sample_v13_high_01 --action view "$@"
