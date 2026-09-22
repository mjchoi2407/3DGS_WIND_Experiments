#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
shape="${1:?씬 이름이 필요합니다}"; shift
phase="${1:-wind}"
case "$phase" in preload|calm|wind) if (($#)); then shift; fi ;; *) phase=wind;; esac
base=experiments/artifacts/runs/teacher_timestep_search
args=(); custom_out=''
while (($#)); do
 case "$1" in
  --sub-pc) base=experiments/artifacts/runs/sub_pc; shift ;;
  --out) custom_out="${2:?출력 경로가 필요합니다}"; shift 2 ;;
  *) args+=("$1"); shift ;;
 esac
done
out="${custom_out:-$base/gauss6_split8_bend500_${shape}_v1}"
exec bash experiments/R1_teacher_velocity_reset/timestep_search/view_gravity_wrinkles.sh "$phase" \
 --out "$out" "${args[@]}"
