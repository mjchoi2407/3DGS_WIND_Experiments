#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
수정된 stump crop PLY 기준으로 filter_3D를 다시 복원하고, r05_alpha_only 주변 mesh 후보를 생성한다.

기본 입력:
  iteration_crop과 iteration_edit 중 더 최근 point_cloud.ply를 자동 선택한다.

생성 흐름:
  1. 각 variation model 폴더에 수정된 crop PLY를 복사한다.
  2. 원본 iteration_30000 PLY에서 filter_3D를 다시 매칭해 붙인다.
  3. 선택한 preset의 파라미터로 mesh extraction을 실행한다.
  4. 생성된 PLY, summary.tsv, sweep.log, README.md를 한 수집 폴더에 모은다.

사용법:
  experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh

실행 전 확인:
  experiments/M04_mesh_extraction/scripts/run_stump_cropfix_r05_mesh_sweep.sh --dry-run

옵션:
      --gpu ID                 CUDA_VISIBLE_DEVICES 값. 기본값: 0.
      --base-model DIR         stump GOF model 디렉터리.
      --crop-iteration NAME    수정된 crop PLY iteration suffix. 기본값: auto.
                              auto는 crop/edit 중 더 최근 PLY를 선택한다.
      --reference-iteration N  filter_3D 복원 reference iteration. 기본값: 30000.
      --preset NAME            후보 preset. 기본값: r05-local.
                              선택: r05-local, r05-filter-sample.
                              r05-filter-sample은 --filter-mesh를 자동 적용한다.
      --output-prefix DIR      variation output prefix. 기본값은 timestamp가 붙은 새 폴더.
      --collect-dir DIR        결과 PLY를 모을 폴더. 기본값은 outputs/collected_meshes 아래 timestamp 폴더.
      --stamp VALUE            로그/요약/출력 폴더에 쓸 고정 timestamp.
      --gof-python PATH        GOF 환경 Python. 기본값: ~/conda-envs/wind3dgs/gof/bin/python.
      --near VALUE             extractor --near 값. 기본값: 0.02.
      --far VALUE              extractor --far 값. 기본값: 1000000.
      --binary-steps N         binary search step 수. 기본값: 8.
      --filter-mesh            extract_mesh.py 계열 --filter_mesh 사용.
      --texture-mesh           vertex color를 붙인다. UV texture는 아니다.
      --force-mesh             같은 output prefix에 기존 mesh가 있으면 지우고 다시 추출한다.
      --dry-run                실제 실행 없이 경로와 command만 출력한다.
  -h, --help                   도움말을 출력한다.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SWEEP_SCRIPT="${SCRIPT_DIR}/run_gof_crop_mesh_param_sweep.sh"
DEFAULT_GOF_PYTHON="${HOME}/conda-envs/wind3dgs/gof/bin/python"

GPU="${GPU:-0}"
BASE_MODEL="${BASE_MODEL:-experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2}"
CROP_ITERATION="${CROP_ITERATION:-auto}"
REFERENCE_ITERATION="${REFERENCE_ITERATION:-30000}"
PRESET="${PRESET:-r05-local}"
OUTPUT_PREFIX="${OUTPUT_PREFIX:-}"
COLLECT_DIR="${COLLECT_DIR:-}"
RUN_STAMP="${RUN_STAMP:-}"
GOF_PYTHON="${GOF_PYTHON:-$DEFAULT_GOF_PYTHON}"
NEAR="${NEAR:-0.02}"
FAR="${FAR:-1000000}"
BINARY_STEPS="${BINARY_STEPS:-8}"
FILTER_MESH="${FILTER_MESH:-0}"
TEXTURE_MESH="${TEXTURE_MESH:-0}"
FORCE_MESH="${FORCE_MESH:-0}"
DRY_RUN="${DRY_RUN:-0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --gpu)
      GPU="$2"
      shift 2
      ;;
    --base-model)
      BASE_MODEL="$2"
      shift 2
      ;;
    --crop-iteration)
      CROP_ITERATION="$2"
      shift 2
      ;;
    --reference-iteration)
      REFERENCE_ITERATION="$2"
      shift 2
      ;;
    --preset)
      PRESET="$2"
      shift 2
      ;;
    --output-prefix)
      OUTPUT_PREFIX="$2"
      shift 2
      ;;
    --collect-dir)
      COLLECT_DIR="$2"
      shift 2
      ;;
    --stamp)
      RUN_STAMP="$2"
      shift 2
      ;;
    --gof-python)
      GOF_PYTHON="$2"
      shift 2
      ;;
    --near)
      NEAR="$2"
      shift 2
      ;;
    --far)
      FAR="$2"
      shift 2
      ;;
    --binary-steps)
      BINARY_STEPS="$2"
      shift 2
      ;;
    --filter-mesh)
      FILTER_MESH=1
      shift
      ;;
    --texture-mesh)
      TEXTURE_MESH=1
      shift
      ;;
    --force-mesh)
      FORCE_MESH=1
      shift
      ;;
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "알 수 없는 옵션: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ "$BASE_MODEL" != /* ]]; then
  BASE_MODEL="${PROJECT_ROOT}/${BASE_MODEL}"
fi
if [[ "$CROP_ITERATION" == "auto" ]]; then
  latest_iteration=""
  latest_mtime=0
  for candidate in crop edit; do
    candidate_ply="${BASE_MODEL}/point_cloud/iteration_${candidate}/point_cloud.ply"
    if [[ ! -f "$candidate_ply" ]]; then
      continue
    fi
    candidate_mtime="$(stat -c '%Y' "$candidate_ply")"
    if (( candidate_mtime > latest_mtime )); then
      latest_mtime="$candidate_mtime"
      latest_iteration="$candidate"
    fi
  done
  if [[ -z "$latest_iteration" ]]; then
    echo "auto crop 선택 실패: iteration_crop/iteration_edit PLY를 찾지 못했다." >&2
    exit 1
  fi
  CROP_ITERATION="$latest_iteration"
fi

case "$PRESET" in
  r05-local)
    RUN_LABEL="r05_local"
    VARIANTS=(
      "r05a_a081_g070 0.81 1.50 0.70 1.00"
      "r05b_a082_g065 0.82 1.50 0.65 1.00"
      "r05c_a082_g070 0.82 1.50 0.70 1.00"
      "r05d_a082_g075 0.82 1.50 0.75 1.00"
      "r05e_a083_g070 0.83 1.50 0.70 1.00"
      "r05f_a084_g070 0.84 1.50 0.70 1.00"
    )
    ;;
  r05-filter-sample)
    RUN_LABEL="r05_filtermesh_sample"
    FILTER_MESH=1
    VARIANTS=(
      "fm_r05c_a082_g070 0.82 1.50 0.70 1.00"
      "fm_r05e_a083_g070 0.83 1.50 0.70 1.00"
      "fm_r05f_a084_g070 0.84 1.50 0.70 1.00"
    )
    ;;
  *)
    echo "알 수 없는 preset: $PRESET" >&2
    echo "선택 가능한 preset: r05-local, r05-filter-sample" >&2
    exit 2
    ;;
esac

if [[ -z "$RUN_STAMP" ]]; then
  RUN_STAMP="$(date +%Y%m%d_%H%M%S)"
fi
if [[ -z "$OUTPUT_PREFIX" ]]; then
  OUTPUT_PREFIX="${BASE_MODEL}_cropfix_${RUN_LABEL}_${RUN_STAMP}"
elif [[ "$OUTPUT_PREFIX" != /* ]]; then
  OUTPUT_PREFIX="${PROJECT_ROOT}/${OUTPUT_PREFIX}"
fi
if [[ -z "$COLLECT_DIR" ]]; then
  COLLECT_DIR="${PROJECT_ROOT}/experiments/M04_mesh_extraction/outputs/collected_meshes/stump_cropfix_${RUN_LABEL}_${RUN_STAMP}"
elif [[ "$COLLECT_DIR" != /* ]]; then
  COLLECT_DIR="${PROJECT_ROOT}/${COLLECT_DIR}"
fi

MODEL_NAME="$(basename "$BASE_MODEL")"
SUMMARY_FILE="${PROJECT_ROOT}/experiments/M04_mesh_extraction/outputs/mesh_param_sweeps/${MODEL_NAME}_${RUN_STAMP}.tsv"
LOG_FILE="${PROJECT_ROOT}/experiments/M04_mesh_extraction/outputs/logs/gof_crop_mesh_param_sweep_${MODEL_NAME}_${RUN_STAMP}.log"
MESH_INDEX="$((BINARY_STEPS - 1))"

require_path() {
  local path="$1"
  local label="$2"
  if [[ ! -e "$path" ]]; then
    echo "${label} 경로가 없다: ${path}" >&2
    exit 1
  fi
}

print_cmd() {
  printf '  '
  printf '%q ' "$@"
  printf '\n'
}

mesh_header_value() {
  local mesh_path="$1"
  local key="$2"
  LC_ALL=C grep -a -m 1 "^element ${key} " "$mesh_path" | awk '{print $3}'
}

require_path "$SWEEP_SCRIPT" "sweep 스크립트"
require_path "$BASE_MODEL/cfg_args" "base cfg_args"
require_path "$BASE_MODEL/cameras.json" "base cameras.json"
require_path "$BASE_MODEL/input.ply" "base input.ply"
require_path "$BASE_MODEL/point_cloud/iteration_${CROP_ITERATION}/point_cloud.ply" "수정된 crop PLY"
require_path "$BASE_MODEL/point_cloud/iteration_${REFERENCE_ITERATION}/point_cloud.ply" "reference PLY"

SWEEP_CMD=(
  "$SWEEP_SCRIPT"
  --gpu "$GPU"
  --base-model "$BASE_MODEL"
  --crop-iteration "$CROP_ITERATION"
  --reference-iteration "$REFERENCE_ITERATION"
  --output-prefix "$OUTPUT_PREFIX"
  --preset "$PRESET"
  --stamp "$RUN_STAMP"
  --gof-python "$GOF_PYTHON"
  --near "$NEAR"
  --far "$FAR"
  --binary-steps "$BINARY_STEPS"
  --force-prepare
)
if [[ "$FILTER_MESH" == "1" ]]; then
  SWEEP_CMD+=(--filter-mesh)
fi
if [[ "$TEXTURE_MESH" == "1" ]]; then
  SWEEP_CMD+=(--texture-mesh)
fi
if [[ "$FORCE_MESH" == "1" ]]; then
  SWEEP_CMD+=(--force-mesh)
fi

if [[ "$DRY_RUN" == "1" ]]; then
  echo "== stump cropfix ${PRESET} dry-run =="
  echo "base_model:          $BASE_MODEL"
  echo "crop_iteration:      $CROP_ITERATION"
  echo "reference_iteration: $REFERENCE_ITERATION"
  echo "preset:              $PRESET"
  echo "filter_mesh:         $FILTER_MESH"
  echo "output_prefix:       $OUTPUT_PREFIX"
  echo "collect_dir:         $COLLECT_DIR"
  echo "stamp:               $RUN_STAMP"
  echo "summary:             $SUMMARY_FILE"
  echo "log:                 $LOG_FILE"
  echo
  echo "실행할 sweep command:"
  print_cmd "${SWEEP_CMD[@]}" --dry-run
  echo
  "${SWEEP_CMD[@]}" --dry-run
  exit 0
fi

echo "== stump cropfix ${PRESET} mesh sweep =="
date '+시작: %Y-%m-%d %H:%M:%S %Z'
echo "수정된 crop PLY: $BASE_MODEL/point_cloud/iteration_${CROP_ITERATION}/point_cloud.ply"
echo "output_prefix: $OUTPUT_PREFIX"
echo "collect_dir:   $COLLECT_DIR"
echo "filter_mesh:   $FILTER_MESH"
echo
echo "sweep command:"
print_cmd "${SWEEP_CMD[@]}"
echo

"${SWEEP_CMD[@]}"

mkdir -p "$COLLECT_DIR"
require_path "$SUMMARY_FILE" "sweep summary"
require_path "$LOG_FILE" "sweep log"
cp -f "$SUMMARY_FILE" "$COLLECT_DIR/summary.tsv"
cp -f "$LOG_FILE" "$COLLECT_DIR/sweep.log"

MANIFEST_FILE="$COLLECT_DIR/manifest.tsv"
printf "label\talpha_threshold\ttetra_scale_multiplier\tgaussian_scale_multiplier\tfilter3d_multiplier\tfilter_mesh\tcollected_mesh\tmesh_bytes\tvertices\tfaces\tfilter3d_summary\n" > "$MANIFEST_FILE"

for variant in "${VARIANTS[@]}"; do
  read -r label alpha tetra gaussian filter3d <<<"$variant"
  mesh_src="${OUTPUT_PREFIX}_${label}/test/ours_${REFERENCE_ITERATION}/fusion/mesh_binary_search_${MESH_INDEX}.ply"
  mesh_dst="${COLLECT_DIR}/${label}_mesh_binary_search_${MESH_INDEX}.ply"
  filter_summary_src="${OUTPUT_PREFIX}_${label}/point_cloud/iteration_${REFERENCE_ITERATION}/point_cloud.filter3d_summary.json"
  filter_summary_dst="${COLLECT_DIR}/${label}_filter3d_summary.json"

  require_path "$mesh_src" "${label} mesh"
  cp -f "$mesh_src" "$mesh_dst"
  if [[ -f "$filter_summary_src" ]]; then
    cp -f "$filter_summary_src" "$filter_summary_dst"
  else
    filter_summary_dst=""
  fi

  mesh_bytes="$(stat -c '%s' "$mesh_dst")"
  vertices="$(mesh_header_value "$mesh_dst" vertex)"
  faces="$(mesh_header_value "$mesh_dst" face)"
  printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n" \
    "$label" "$alpha" "$tetra" "$gaussian" "$filter3d" "$FILTER_MESH" "$mesh_dst" "$mesh_bytes" \
    "${vertices:-unknown}" "${faces:-unknown}" "$filter_summary_dst" >> "$MANIFEST_FILE"
done

WINDOWS_PATH=""
if command -v wslpath >/dev/null 2>&1; then
  WINDOWS_PATH="$(wslpath -w "$COLLECT_DIR" 2>/dev/null || true)"
fi

cat > "$COLLECT_DIR/README.md" <<EOF
# stump cropfix ${PRESET} mesh sweep

수정된 stump crop PLY에서 \`filter_3D\`를 다시 복원하고, 이전 best 후보였던 \`r05_alpha_only\` 주변을 좁게 테스트한 결과 폴더다.

- 실행 시각: ${RUN_STAMP}
- base model: \`${BASE_MODEL}\`
- crop iteration: \`${CROP_ITERATION}\`
- reference iteration: \`${REFERENCE_ITERATION}\`
- preset: \`${PRESET}\`
- filter_mesh: \`${FILTER_MESH}\`
- output prefix: \`${OUTPUT_PREFIX}\`
- summary: \`summary.tsv\`
- manifest: \`manifest.tsv\`
- log: \`sweep.log\`

## 후보

| label | alpha | tetra | gaussian |
|---|---:|---:|---:|
EOF

for variant in "${VARIANTS[@]}"; do
  read -r label alpha tetra gaussian _ <<<"$variant"
  printf '| %s | %s | %s | %s |\n' "$label" "$alpha" "$tetra" "$gaussian" >> "$COLLECT_DIR/README.md"
done

cat >> "$COLLECT_DIR/README.md" <<'EOF'

## 확인 방법

후보를 표 순서대로 비교한다. `filter_mesh=1` 결과는 같은 alpha/tetra/gaussian 값을 사용한 이전 무필터 결과와 함께 확인한다.
EOF

echo
date '+종료: %Y-%m-%d %H:%M:%S %Z'
echo "status: OK"
echo "수집 폴더: $COLLECT_DIR"
if [[ -n "$WINDOWS_PATH" ]]; then
  echo "Windows 탐색기 경로: $WINDOWS_PATH"
fi
echo "manifest: $MANIFEST_FILE"
