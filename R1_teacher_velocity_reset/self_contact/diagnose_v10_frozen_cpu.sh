#!/usr/bin/env bash
# 메인에서 한 번 생성한 동일 CPU 계수 파일을 양쪽 PC에 공급한다.
# 기존 v10 본 실행/계수 비동결 대조 경로는 변경하지 않는다.
set -euo pipefail
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace=$(cd -- "$script_dir/../../.." && pwd)
cpu_input="$workspace/experiments/artifacts/runs/p3_self_contact/diagnostics/20260922T155046Z-dddbdc49008c4cd6ba1eea917fd03bbd_main_cpu_frozen/cpu_inputs.npz"
cpu_sha=c742796976565b56bb30b3b10630f65555d8d2a8517ceb5c1d18034ac4d7bf8e
exec bash "$script_dir/diagnose_v10_repro.sh" "$@" \
  --frozen-cpu "$cpu_input" --expected-frozen-cpu-sha256 "$cpu_sha"
