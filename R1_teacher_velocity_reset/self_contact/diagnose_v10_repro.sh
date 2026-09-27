#!/usr/bin/env bash
# 별도 진단만 실행한다. 기존 세 씬 wrapper·run에는 쓰지 않는다.
set -euo pipefail
workspace=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)
computer=''
mode=''
sample=preload_first
repeats=3
focus=0
frozen_cpu=''
frozen_cpu_sha=''
while (($#)); do
  case "$1" in
    --computer) computer=$2; shift 2 ;;
    --mode) mode=$2; shift 2 ;;
    --case) sample=$2; shift 2 ;;
    --repeats) repeats=$2; shift 2 ;;
    --focus-substep) focus=$2; shift 2 ;;
    --frozen-cpu) frozen_cpu=$2; shift 2 ;;
    --expected-frozen-cpu-sha256) frozen_cpu_sha=$2; shift 2 ;;
    --help|-h)
      printf '%s\n' '사용: bash diagnose_v10_repro.sh --computer main|sub --mode host|replay|massprobe|plain|memcheck|initcheck|racecheck|synccheck [--case preload_first|wind10|wind115|sub_wind115|wind121] [--repeats 1..5] [--focus-substep 0-based]'
      printf '%s\n' 'host: CPU 입력만 기록. replay: 한 프레임 대조. massprobe: 동결 CPU에서 질량 풀이 전후 원시 벡터 기록. plain: 비계측 대조. 기존 run 수정 없음.'
      printf '%s\n' 'CPU 동결: --frozen-cpu 공통.npz --expected-frozen-cpu-sha256 고정SHA256 (두 옵션을 함께 지정)'
      exit 0 ;;
    *) printf '알 수 없는 옵션: %s\n' "$1" >&2; exit 2 ;;
  esac
done
main_run="$workspace/experiments/artifacts/runs/p3_self_contact/three_scenes_gpu_bend500_manual_v10"
case "$computer" in
  main)
    run_root=$main_run
    output_base="$workspace/experiments/artifacts/runs/p3_self_contact/diagnostics"
    diagnostic_python=${WIND3DGS_PYTHON:-"$workspace/.venv/bin/python"}
    ;;
  sub)
    mountpoint -q /mnt/wind3dgs-sub-results || { printf '%s\n' '서브 결과 공유 마운트가 필요합니다.' >&2; exit 2; }
    run_root=/mnt/wind3dgs-sub-results/20260922T134104Z-1515e916c2144b25bc5d37b7316c3120/simulation
    output_base=/mnt/wind3dgs-sub-results/diagnostics
    diagnostic_python=${WIND3DGS_PYTHON:-python3}
    ;;
  *) printf '%s\n' '--computer main 또는 sub를 지정하세요.' >&2; exit 2 ;;
esac
case "$sample" in
  preload_first)
    phase=preload; frame=0; initial=initial_state.npz
    initial_sha=fd3db24c136fc9691e29ced99de53cfcbe42ed10a0dcf9b316b0b0002d715ab7 ;;
  wind10)
    phase=wind; frame=9; initial=frame_0008.npz
    initial_sha=1d00c26ca603f0d0208207e9403cbbd4165340a64f75290dd23505ca70aa12a7 ;;
  wind115)
    phase=wind; frame=114; initial=frame_0113.npz
    initial_sha=1d5663d129438fcb6c5fa9b866b191ace0a00a256fb094ba39ab6d39d2dcdba9 ;;
  sub_wind115)
    phase=wind; frame=114; initial=frame_0113.npz
    initial_sha=80b11379c8b1d78c7553317581447fdab1b03d90bc379509ac0ec482ded24bdc ;;
  wind121)
    phase=wind; frame=120; initial=frame_0119.npz
    initial_sha=ffd297564c989096854e07b30e21b32b146c12adf2b8fcb629f0b9f9f2faaa96 ;;
  *) printf '알 수 없는 진단 사례: %s\n' "$sample" >&2; exit 2 ;;
esac
frame_start="$main_run/reference_rectangle/outputs/$phase/$initial"
if [[ "$sample" == sub_wind115 ]]; then
  if [[ "$computer" == main ]]; then
    frame_start="$workspace/experiments/artifacts/runs/sub_pc/20260922T134104Z-1515e916c2144b25bc5d37b7316c3120/simulation/reference_rectangle/outputs/wind/$initial"
  else
    frame_start="$run_root/reference_rectangle/outputs/wind/$initial"
  fi
fi
extra=()
if [[ -n "$frozen_cpu" || -n "$frozen_cpu_sha" ]]; then
  [[ -f "$frozen_cpu" && "$frozen_cpu_sha" =~ ^[0-9a-f]{64}$ ]] || { printf '%s\n' '공통 CPU NPZ 파일과 고정 SHA256이 모두 필요합니다.' >&2; exit 2; }
  extra+=(--frozen-cpu "$frozen_cpu" --expected-frozen-cpu-sha256 "$frozen_cpu_sha")
fi
case "$mode" in
  host) extra+=(--host-only) ;;
  replay) ;;
  massprobe) extra+=(--mass-probe) ;;
  plain) extra+=(--uninstrumented) ;;
  memcheck|initcheck|racecheck|synccheck) extra+=(--sanitizer "$mode"); repeats=1 ;;
  *) printf '%s\n' '--mode를 지정하세요. 먼저 host, 이후 replay를 권장합니다.' >&2; exit 2 ;;
esac
case "$repeats" in 1|2|3|4|5) ;; *) printf '%s\n' '--repeats는 1..5입니다.' >&2; exit 2 ;; esac
[[ "$focus" =~ ^[0-9]+$ ]] || { printf '%s\n' '--focus-substep은 0 이상의 정수입니다.' >&2; exit 2; }
run_id=$("$diagnostic_python" -c 'from datetime import datetime, timezone; import uuid; print(datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")+"-"+uuid.uuid4().hex)')
out="$output_base/${run_id}_${computer}_${sample}_${mode}"
printf '새 진단 출력: %s\n' "$out"
export PYTHONDONTWRITEBYTECODE=1
exec "$diagnostic_python" "$workspace/code/wind3dgs/evaluation/contact_determinism.py" replay \
  --root "$run_root" --out "$out" \
  --frame-start "$frame_start" \
  --expected-start-sha256 "$initial_sha" --phase "$phase" --frame "$frame" \
  --repeats "$repeats" --focus-substep "$focus" "${extra[@]}"
