#!/usr/bin/env bash
# 현재 컴퓨터의 RTX 5070에서 체크포인트 3회 재생 및 별도 Nsight Systems 수집.
set -euo pipefail
exec bash "$(dirname -- "${BASH_SOURCE[0]}")/run_newmark_gauss_retry.sh" --profile "$@"
