#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.."
phase="${1:-wind}"
case "$phase" in preload|calm|wind) if (($#)); then shift; fi ;; *) printf '%s\n' '사용법: view_gravity_wrinkles.sh [preload|calm|wind] [--out 경로] [뷰어 옵션]' >&2; exit 2 ;; esac
out=experiments/artifacts/runs/teacher_timestep_search/gravity_wrinkles_flag_hilo_v1
if [[ "${1:-}" == --out ]]; then out="$2"; shift 2; fi
shape="$(.venv/bin/python -c 'import json,sys;print(json.load(open(sys.argv[1]))["shape"])' "$out/config.json")"
export PYTHONPATH="$out/runtime/code"
export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1
if [[ -z "${DISPLAY:-}" && -S /mnt/wslg/.X11-unix/X0 ]]; then export DISPLAY=:0; fi
printf '%s\n' '국소 기하 검산 결과입니다. 자기 교차/접촉 응답은 미포함이며 학습 적격 데이터가 아닙니다.'
exec .venv/bin/python -m wind3dgs.evaluation.view_shell_recording --run "$out/$phase" --shape "$shape" --cache "$out/playback/$phase" "$@"
