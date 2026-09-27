#!/usr/bin/env bash
# 동일한 동결 질량행렬과 첫 RHS만 풀이한다. 원래 프레임·체크포인트를 실행하지 않는다.
set -euo pipefail
workspace=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)
computer=''
repeats=3
cycles=4
cudss_deterministic=0
while (($#)); do
  case "$1" in
    --computer) computer=$2; shift 2 ;;
    --repeats) repeats=$2; shift 2 ;;
    --cycles) cycles=$2; shift 2 ;;
    --cudss-deterministic) cudss_deterministic=1; shift ;;
    --help|-h)
      printf '%s\n' '사용: bash diagnose_v10_mass_only.sh --computer main|sub [--repeats 2..5] [--cycles 2..8] [--cudss-deterministic]'
      printf '%s\n' '고정 CSR/RHS의 cuDSS graph·직접 풀이만 반복. 기존 run은 읽기만 하고 새 UUID 출력 사용.'
      exit 0 ;;
    *) printf '알 수 없는 옵션: %s\n' "$1" >&2; exit 2 ;;
  esac
done
case "$repeats" in 2|3|4|5) ;; *) printf '%s\n' '--repeats는 2..5입니다.' >&2; exit 2 ;; esac
case "$cycles" in 2|3|4|5|6|7|8) ;; *) printf '%s\n' '--cycles는 2..8입니다.' >&2; exit 2 ;; esac
case "$computer" in
  main)
    run_root="$workspace/experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v10"
    output_base="$workspace/experiments/artifacts/runs/p3_self_contact/diagnostics"
    diagnostic_python=${WIND3DGS_PYTHON:-"$workspace/.venv/bin/python"} ;;
  sub)
    mountpoint -q /mnt/wind3dgs-sub-results || { printf '%s\n' '서브 결과 공유 마운트가 필요합니다.' >&2; exit 2; }
    run_root=/mnt/wind3dgs-sub-results/20260922T134104Z-1515e916c2144b25bc5d37b7316c3120/simulation
    output_base=/mnt/wind3dgs-sub-results/diagnostics
    diagnostic_python=${WIND3DGS_PYTHON:-python3} ;;
  *) printf '%s\n' '--computer main 또는 sub를 지정하세요.' >&2; exit 2 ;;
esac
source_trial="$workspace/experiments/artifacts/runs/p3_self_contact/diagnostics/20260923T004520Z-77ed63f3d4cf49b9900fad78a833c3cf_main_preload_first_massprobe/trial_00"
cpu_input="$workspace/experiments/artifacts/runs/p3_self_contact/diagnostics/20260922T155046Z-dddbdc49008c4cd6ba1eea917fd03bbd_main_cpu_frozen/cpu_inputs.npz"
cpu_sha=c742796976565b56bb30b3b10630f65555d8d2a8517ceb5c1d18034ac4d7bf8e
rhs_sha=4e893ab72dc5b90d0c57446e3c0aae3e993203594d022c5973ab6ae8fc802c52
run_id=$("$diagnostic_python" -c 'from datetime import datetime, timezone; import uuid; print(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex)')
mode_suffix=''
deterministic_args=()
if ((cudss_deterministic)); then
  mode_suffix='_cudss_deterministic'
  deterministic_args=(--cudss-deterministic)
fi
out="$output_base/${run_id}_${computer}_preload_mass_only${mode_suffix}"
printf '새 독립 질량 풀이 출력: %s\n' "$out"
export PYTHONDONTWRITEBYTECODE=1
exec "$diagnostic_python" "$workspace/code/wind3dgs/evaluation/contact_mass_isolation.py" run \
  --cpu "$cpu_input" --source-trial "$source_trial" --run-root "$run_root" --out "$out" \
  --expected-cpu "$cpu_sha" --expected-rhs "$rhs_sha" --repeats "$repeats" --cycles "$cycles" \
  "${deterministic_args[@]}"
