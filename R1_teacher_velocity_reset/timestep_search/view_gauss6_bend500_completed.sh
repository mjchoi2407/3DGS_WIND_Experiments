#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
shape="${1:?reference_rectangle / triangular_flag / handkerchief 중 씬을 지정하세요}"; shift
case "$shape" in
 reference_rectangle) out=experiments/artifacts/runs/teacher_timestep_search/gauss6_split8_bend500_reference_rectangle_v1 ;;
 triangular_flag) out=experiments/artifacts/runs/sub_pc/20260914T033418Z-4c977dfc6d2e4e5295ead7991dd58962/simulation ;;
 handkerchief) out=experiments/artifacts/runs/sub_pc/20260914T033603Z-f402b992660342b0a8a0bbf83fe967ea/simulation ;;
 *) echo '지원하지 않는 씬입니다.' >&2; exit 2 ;;
esac
phase="${1:-wind}"
case "$phase" in preload|calm|wind) if (($#)); then shift; fi ;; *) phase=wind ;; esac
exec bash experiments/R1_teacher_velocity_reset/timestep_search/view_gauss6_bend500.sh "$shape" "$phase" --out "$out" "$@"
