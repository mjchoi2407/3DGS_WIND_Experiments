#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
# 현행 재시도는 Gauss6차8분할이다. 기존 half-dt 결과는 새 출력과 분리한다.
exec bash experiments/R1_teacher_velocity_reset/timestep_search/run_newmark_gauss_retry.sh "$@"
