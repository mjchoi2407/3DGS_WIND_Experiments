#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
GOF crop mesh extraction 파라미터 5개 variation을 한 번에 생성한다.

사용법:
  experiments/M04_mesh_extraction/scripts/run_gof_crop_mesh_param_sweep.sh \
    --base-model experiments/M04_mesh_extraction/models/gof_mip360_stump_i30000_fullres_highplus2

기본 variation:
  v01_base      alpha=0.50, tetra=3.00, gaussian=1.00, filter3d=1.00
  v02_alpha60   alpha=0.60, tetra=3.00, gaussian=1.00, filter3d=1.00
  v03_balanced  alpha=0.70, tetra=2.50, gaussian=0.90, filter3d=1.00
  v04_thinner   alpha=0.75, tetra=2.00, gaussian=0.80, filter3d=1.00
  v05_aggressive alpha=0.80, tetra=1.50, gaussian=0.70, filter3d=1.00

추가 preset:
  aggressive-extra:
    v06_a082_g065 alpha=0.82, tetra=1.40, gaussian=0.65, filter3d=1.00
    v07_a085_g060 alpha=0.85, tetra=1.30, gaussian=0.60, filter3d=1.00
    v08_a088_g055 alpha=0.88, tetra=1.20, gaussian=0.55, filter3d=1.00
    v09_a090_g050 alpha=0.90, tetra=1.10, gaussian=0.50, filter3d=1.00
    v10_a092_g045 alpha=0.92, tetra=1.00, gaussian=0.45, filter3d=1.00
  v05-refine:
    r01_v05_dense       alpha=0.80, tetra=1.25, gaussian=0.70, filter3d=1.00
    r02_v05_dense_plus  alpha=0.80, tetra=1.00, gaussian=0.70, filter3d=1.00
    r03_soft_dense      alpha=0.78, tetra=1.25, gaussian=0.75, filter3d=1.00
    r04_soft_dense_plus alpha=0.78, tetra=1.00, gaussian=0.75, filter3d=1.00
    r05_alpha_only      alpha=0.82, tetra=1.50, gaussian=0.70, filter3d=1.00
  r05-local:
    r05a_a081_g070      alpha=0.81, tetra=1.50, gaussian=0.70, filter3d=1.00
    r05b_a082_g065      alpha=0.82, tetra=1.50, gaussian=0.65, filter3d=1.00
    r05c_a082_g070      alpha=0.82, tetra=1.50, gaussian=0.70, filter3d=1.00
    r05d_a082_g075      alpha=0.82, tetra=1.50, gaussian=0.75, filter3d=1.00
    r05e_a083_g070      alpha=0.83, tetra=1.50, gaussian=0.70, filter3d=1.00
    r05f_a084_g070      alpha=0.84, tetra=1.50, gaussian=0.70, filter3d=1.00
  r05-filter-sample:
    fm_r05c_a082_g070   alpha=0.82, tetra=1.50, gaussian=0.70, filter3d=1.00
    fm_r05e_a083_g070   alpha=0.83, tetra=1.50, gaussian=0.70, filter3d=1.00
    fm_r05f_a084_g070   alpha=0.84, tetra=1.50, gaussian=0.70, filter3d=1.00

옵션:
      --gpu ID                 CUDA_VISIBLE_DEVICES 값. 기본값: 0.
      --base-model DIR         원본 GOF model 디렉터리. 필수.
      --crop-iteration NAME    crop PLY iteration suffix. 기본값: crop.
      --reference-iteration N  filter_3D 복원 reference iteration. 기본값: 30000.
      --output-prefix DIR      variation output prefix. 기본값: <base-model>_crop_mesh_param.
      --preset NAME            variation preset. 기본값: default.
                              선택: default, aggressive-extra, v05-refine,
                              r05-local, r05-filter-sample.
      --stamp VALUE            로그/요약 파일명에 쓸 고정 timestamp.
      --gof-python PATH        GOF 환경 Python. 기본값: ~/conda-envs/wind3dgs/gof/bin/python.
      --near VALUE             extractor --near 값. 기본값: 0.02.
      --far VALUE              extractor --far 값. 기본값: 1000000.
      --binary-steps N         binary search step 수. 기본값: 8.
      --filter-mesh            extract_mesh.py 계열 --filter_mesh 사용.
      --texture-mesh           vertex color를 붙인다. UV texture는 아니다.
      --force-prepare          복원된 crop PLY가 있어도 다시 만든다.
      --force-mesh             기존 variation mesh/cells를 지우고 다시 추출한다.
      --dry-run                실제 실행 없이 경로와 command만 출력한다.
  -h, --help                   도움말을 출력한다.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
GOF_DIR="${PROJECT_ROOT}/external/gaussian-opacity-fields"
DEFAULT_GOF_PYTHON="${HOME}/conda-envs/wind3dgs/gof/bin/python"

GPU="${GPU:-0}"
BASE_MODEL="${BASE_MODEL:-}"
CROP_ITERATION="${CROP_ITERATION:-crop}"
REFERENCE_ITERATION="${REFERENCE_ITERATION:-30000}"
OUTPUT_PREFIX="${OUTPUT_PREFIX:-}"
PRESET="${PRESET:-default}"
RUN_STAMP="${RUN_STAMP:-}"
GOF_PYTHON="${GOF_PYTHON:-$DEFAULT_GOF_PYTHON}"
NEAR="${NEAR:-0.02}"
FAR="${FAR:-1000000}"
BINARY_STEPS="${BINARY_STEPS:-8}"
FILTER_MESH="${FILTER_MESH:-0}"
TEXTURE_MESH="${TEXTURE_MESH:-0}"
FORCE_PREPARE="${FORCE_PREPARE:-0}"
FORCE_MESH="${FORCE_MESH:-0}"
DRY_RUN="${DRY_RUN:-0}"
OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl-gof}"

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
    --output-prefix)
      OUTPUT_PREFIX="$2"
      shift 2
      ;;
    --preset)
      PRESET="$2"
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
    --force-prepare)
      FORCE_PREPARE=1
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

if [[ -z "$BASE_MODEL" ]]; then
  echo "--base-model은 필수다." >&2
  usage >&2
  exit 2
fi

if [[ "$BASE_MODEL" != /* ]]; then
  BASE_MODEL="${PROJECT_ROOT}/${BASE_MODEL}"
fi
if [[ -z "$OUTPUT_PREFIX" ]]; then
  OUTPUT_PREFIX="${BASE_MODEL}_crop_mesh_param"
elif [[ "$OUTPUT_PREFIX" != /* ]]; then
  OUTPUT_PREFIX="${PROJECT_ROOT}/${OUTPUT_PREFIX}"
fi

MODEL_NAME="$(basename "$BASE_MODEL")"
RESTORE_SCRIPT="${SCRIPT_DIR}/restore_gof_filter3d_from_reference.py"
PARAM_EXTRACTOR="${SCRIPT_DIR}/extract_mesh_parametric.py"
CROP_PLY="${BASE_MODEL}/point_cloud/iteration_${CROP_ITERATION}/point_cloud.ply"
REFERENCE_PLY="${BASE_MODEL}/point_cloud/iteration_${REFERENCE_ITERATION}/point_cloud.ply"
LOG_DIR="${PROJECT_ROOT}/experiments/M04_mesh_extraction/outputs/logs"
SUMMARY_DIR="${PROJECT_ROOT}/experiments/M04_mesh_extraction/outputs/mesh_param_sweeps"
if [[ -z "$RUN_STAMP" ]]; then
  RUN_STAMP="$(date +%Y%m%d_%H%M%S)"
fi
STAMP="$RUN_STAMP"
LOG_FILE="${LOG_DIR}/gof_crop_mesh_param_sweep_${MODEL_NAME}_${STAMP}.log"
SUMMARY_FILE="${SUMMARY_DIR}/${MODEL_NAME}_${STAMP}.tsv"

case "$PRESET" in
  default)
    VARIANTS=(
      "v01_base 0.50 3.00 1.00 1.00"
      "v02_alpha60 0.60 3.00 1.00 1.00"
      "v03_balanced 0.70 2.50 0.90 1.00"
      "v04_thinner 0.75 2.00 0.80 1.00"
      "v05_aggressive 0.80 1.50 0.70 1.00"
    )
    ;;
  aggressive-extra)
    VARIANTS=(
      "v06_a082_g065 0.82 1.40 0.65 1.00"
      "v07_a085_g060 0.85 1.30 0.60 1.00"
      "v08_a088_g055 0.88 1.20 0.55 1.00"
      "v09_a090_g050 0.90 1.10 0.50 1.00"
      "v10_a092_g045 0.92 1.00 0.45 1.00"
    )
    ;;
  v05-refine)
    VARIANTS=(
      "r01_v05_dense 0.80 1.25 0.70 1.00"
      "r02_v05_dense_plus 0.80 1.00 0.70 1.00"
      "r03_soft_dense 0.78 1.25 0.75 1.00"
      "r04_soft_dense_plus 0.78 1.00 0.75 1.00"
      "r05_alpha_only 0.82 1.50 0.70 1.00"
    )
    ;;
  r05-local)
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
    VARIANTS=(
      "fm_r05c_a082_g070 0.82 1.50 0.70 1.00"
      "fm_r05e_a083_g070 0.83 1.50 0.70 1.00"
      "fm_r05f_a084_g070 0.84 1.50 0.70 1.00"
    )
    ;;
  *)
    echo "알 수 없는 preset: $PRESET" >&2
    echo "선택 가능한 preset: default, aggressive-extra, v05-refine, r05-local, r05-filter-sample" >&2
    exit 2
    ;;
esac

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

require_path "$RESTORE_SCRIPT" "filter_3D 복원 스크립트"
require_path "$PARAM_EXTRACTOR" "파라미터 extractor"
require_path "$GOF_DIR/extract_mesh.py" "GOF extract_mesh.py"
require_path "$GOF_PYTHON" "GOF Python"
require_path "$BASE_MODEL/cfg_args" "base cfg_args"
require_path "$BASE_MODEL/cameras.json" "base cameras.json"
require_path "$BASE_MODEL/input.ply" "base input.ply"
require_path "$CROP_PLY" "crop PLY"
require_path "$REFERENCE_PLY" "reference PLY"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "== GOF crop mesh param sweep dry-run =="
  echo "base_model:      $BASE_MODEL"
  echo "output_prefix:   $OUTPUT_PREFIX"
  echo "preset:          $PRESET"
  echo "stamp:           $STAMP"
  echo "log:             $LOG_FILE"
  echo "summary:         $SUMMARY_FILE"
  echo "variants:"
  for variant in "${VARIANTS[@]}"; do
    read -r label alpha tetra gaussian filter3d <<<"$variant"
    output_model="${OUTPUT_PREFIX}_${label}"
    mesh_cmd=(
      "$GOF_PYTHON" "$PARAM_EXTRACTOR"
      -m "$output_model"
      --iteration "$REFERENCE_ITERATION"
      --near "$NEAR"
      --far "$FAR"
      --alpha-threshold "$alpha"
      --tetra-scale-multiplier "$tetra"
      --gaussian-scale-multiplier "$gaussian"
      --filter3d-multiplier "$filter3d"
      --binary-steps "$BINARY_STEPS"
    )
    if [[ "$FILTER_MESH" == "1" ]]; then
      mesh_cmd+=(--filter_mesh)
    fi
    if [[ "$TEXTURE_MESH" == "1" ]]; then
      mesh_cmd+=(--texture_mesh)
    fi
    echo "  $label -> $output_model"
    print_cmd "${mesh_cmd[@]}"
  done
  exit 0
fi

mkdir -p "$LOG_DIR" "$SUMMARY_DIR" "$MPLCONFIGDIR"
exec > >(tee "$LOG_FILE") 2>&1

echo "== GOF crop mesh param sweep =="
date '+시작: %Y-%m-%d %H:%M:%S %Z'
echo "project:             $PROJECT_ROOT"
echo "base_model:          $BASE_MODEL"
echo "model_name:          $MODEL_NAME"
echo "crop_ply:            $CROP_PLY"
echo "reference_ply:       $REFERENCE_PLY"
echo "output_prefix:       $OUTPUT_PREFIX"
echo "preset:              $PRESET"
echo "stamp:               $STAMP"
echo "gof_dir:             $GOF_DIR"
echo "python:              $GOF_PYTHON"
echo "gpu:                 $GPU"
echo "omp threads:         $OMP_NUM_THREADS"
echo "mplconfigdir:        $MPLCONFIGDIR"
echo "near/far:            $NEAR / $FAR"
echo "binary_steps:        $BINARY_STEPS"
echo "filter_mesh:         $FILTER_MESH"
echo "texture_mesh:        $TEXTURE_MESH"
echo "force_prepare:       $FORCE_PREPARE"
echo "force_mesh:          $FORCE_MESH"
echo "log:                 $LOG_FILE"
echo "summary:             $SUMMARY_FILE"
echo

echo "GPU 사전 확인:"
CUDA_VISIBLE_DEVICES="$GPU" "$GOF_PYTHON" - <<'PY'
import sys
import torch

print(f"  torch: {torch.__version__}")
print(f"  cuda_available: {torch.cuda.is_available()}")
if not torch.cuda.is_available():
    print("  오류: 이 터미널에서 CUDA를 사용할 수 없습니다.")
    sys.exit(3)
print(f"  cuda_device_count: {torch.cuda.device_count()}")
print(f"  cuda_device_0: {torch.cuda.get_device_name(0)}")
try:
    free_bytes, total_bytes = torch.cuda.mem_get_info()
except Exception as exc:
    print(f"  cuda_mem_info: 확인 불가 ({exc})")
else:
    print(f"  cuda_mem_free_gib: {free_bytes / (1024 ** 3):.2f}")
    print(f"  cuda_mem_total_gib: {total_bytes / (1024 ** 3):.2f}")
PY

printf "label\talpha_threshold\ttetra_scale_multiplier\tgaussian_scale_multiplier\tfilter3d_multiplier\tmesh_path\tmesh_bytes\tstatus\n" > "$SUMMARY_FILE"

for variant in "${VARIANTS[@]}"; do
  read -r label alpha tetra gaussian filter3d <<<"$variant"
  output_model="${OUTPUT_PREFIX}_${label}"
  output_ply="${output_model}/point_cloud/iteration_${REFERENCE_ITERATION}/point_cloud.ply"
  summary_json="${output_model}/point_cloud/iteration_${REFERENCE_ITERATION}/point_cloud.filter3d_summary.json"
  fusion_dir="${output_model}/test/ours_${REFERENCE_ITERATION}/fusion"
  mesh_path="${fusion_dir}/mesh_binary_search_$((BINARY_STEPS - 1)).ply"

  echo
  echo "== variation: $label =="
  echo "alpha_threshold:          $alpha"
  echo "tetra_scale_multiplier:   $tetra"
  echo "gaussian_scale_multiplier:$gaussian"
  echo "filter3d_multiplier:      $filter3d"
  echo "output_model:             $output_model"
  echo "mesh:                     $mesh_path"

  mkdir -p "$output_model" "$(dirname "$output_ply")"
  cp -f "$BASE_MODEL/cfg_args" "$output_model/cfg_args"
  cp -f "$BASE_MODEL/cameras.json" "$output_model/cameras.json"
  cp -f "$BASE_MODEL/input.ply" "$output_model/input.ply"

  if [[ "$FORCE_PREPARE" == "1" || ! -f "$output_ply" ]]; then
    echo "crop PLY에 filter_3D를 복원한다."
    "$GOF_PYTHON" "$RESTORE_SCRIPT" \
      --input "$CROP_PLY" \
      --reference "$REFERENCE_PLY" \
      --output "$output_ply" \
      --summary "$summary_json"
  else
    echo "복원된 crop PLY를 재사용한다: $output_ply"
  fi

  if [[ "$FORCE_MESH" == "1" && -d "$fusion_dir" ]]; then
    echo "기존 variation fusion 산출물을 제거한다: $fusion_dir"
    rm -f "$fusion_dir"/cells.pt "$fusion_dir"/mesh_binary_search_*.ply "$fusion_dir"/parametric_mesh_summary.json
  fi

  if [[ -f "$mesh_path" && "$FORCE_MESH" != "1" ]]; then
    echo "mesh가 이미 있어서 재사용한다."
  else
    mesh_cmd=(
      "$GOF_PYTHON" "$PARAM_EXTRACTOR"
      -m "$output_model"
      --iteration "$REFERENCE_ITERATION"
      --near "$NEAR"
      --far "$FAR"
      --alpha-threshold "$alpha"
      --tetra-scale-multiplier "$tetra"
      --gaussian-scale-multiplier "$gaussian"
      --filter3d-multiplier "$filter3d"
      --binary-steps "$BINARY_STEPS"
    )
    if [[ "$FILTER_MESH" == "1" ]]; then
      mesh_cmd+=(--filter_mesh)
    fi
    if [[ "$TEXTURE_MESH" == "1" ]]; then
      mesh_cmd+=(--texture_mesh)
    fi

    echo "mesh extraction command:"
    print_cmd "${mesh_cmd[@]}"
    (
      cd "$GOF_DIR"
      export CUDA_VISIBLE_DEVICES="$GPU"
      export OMP_NUM_THREADS="$OMP_NUM_THREADS"
      export MPLCONFIGDIR="$MPLCONFIGDIR"
      "${mesh_cmd[@]}"
    )
  fi

  if [[ -f "$mesh_path" ]]; then
    mesh_bytes="$(stat -c '%s' "$mesh_path")"
    printf "%s\t%s\t%s\t%s\t%s\t%s\t%s\tOK\n" \
      "$label" "$alpha" "$tetra" "$gaussian" "$filter3d" "$mesh_path" "$mesh_bytes" >> "$SUMMARY_FILE"
    stat -c 'mesh 생성 확인: %n %s bytes' "$mesh_path"
  else
    printf "%s\t%s\t%s\t%s\t%s\t%s\t0\tFAIL\n" \
      "$label" "$alpha" "$tetra" "$gaussian" "$filter3d" "$mesh_path" >> "$SUMMARY_FILE"
    echo "mesh 파일이 없다: $mesh_path" >&2
    exit 4
  fi
done

echo
date '+종료: %Y-%m-%d %H:%M:%S %Z'
echo "status: OK"
echo "summary: $SUMMARY_FILE"
echo "log: $LOG_FILE"
