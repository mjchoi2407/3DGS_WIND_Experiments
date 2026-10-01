#!/usr/bin/env bash
# 기본 candidate는 서브 컴 완료 v13. 실제 비교에는 더 정밀한 --reference가 필요하다.
# --self-check는 동일 원본의 연결 검사이며 민감도 통과를 뜻하지 않는다.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
comparison_stamp=$(date -u +%Y%m%dT%H%M%S%NZ)
comparison_source=experiments/artifacts/runs/sub_pc/20260928T043613Z-b306cdad658642d089bb9b2330f8fdae/simulation
comparison_options=(--axis time)
if [[ "${1:-}" == --self-check ]]; then
  shift
  comparison_options=(--axis identity-check --reference "$comparison_source")
elif [[ $# -eq 0 ]]; then
  echo '실제 시간 비교에는 더 정밀한 완료 run을 --reference로 지정하세요.' >&2
  echo '연결만 점검하려면 --self-check를 사용하세요. 새 시뮬레이션은 실행하지 않습니다.' >&2
  exit 2
fi
exec bash experiments/R1_teacher_velocity_reset/self_contact/compare_gpu_cg_checks.sh \
  --candidate "$comparison_source" "${comparison_options[@]}" \
  --out "experiments/artifacts/runs/p3_self_contact/cg_comparison/v13_sub_${comparison_stamp}" "$@"
