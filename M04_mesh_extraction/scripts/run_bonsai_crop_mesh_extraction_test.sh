#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
bonsai crop PLY를 GOF mesh extraction으로 테스트한다.

사용법:
  experiments/M04_mesh_extraction/scripts/run_bonsai_crop_mesh_extraction_test.sh

옵션:
      --gpu ID                 CUDA_VISIBLE_DEVICES 값. 기본값: 0.
      --base-model DIR         원본 bonsai GOF model 디렉터리.
      --crop-iteration NAME    crop PLY iteration suffix. 기본값: crop.
      --reference-iteration N  filter_3D 복원에 쓸 원본 iteration. 기본값: 30000.
      --output-model DIR       임시 crop mesh test model 디렉터리.
      --output-iteration N     extract_mesh.py에 넘길 iteration. 기본값: 30000.
      --gof-python PATH        GOF 환경 Python. 기본값: ~/conda-envs/wind3dgs/gof/bin/python.
      --filter-mesh            extract_mesh.py --filter_mesh 사용.
      --texture-mesh           extract_mesh.py --texture_mesh 사용.
      --near VALUE             extract_mesh.py --near 값. 기본값: 0.02.
      --far VALUE              extract_mesh.py --far 값. 기본값: 1000000.
      --force-prepare          복원된 crop PLY가 있어도 다시 만든다.
      --dry-run                실제 실행 없이 경로와 command만 출력한다.
  -h, --help                   도움말을 출력한다.
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
GOF_DIR="${PROJECT_ROOT}/external/gaussian-opacity-fields"
DEFAULT_BASE_MODEL="${PROJECT_ROOT}/experiments/M04_mesh_extraction/models/gof_mip360_bonsai_i30000_images_2"
DEFAULT_OUTPUT_MODEL="${PROJECT_ROOT}/experiments/M04_mesh_extraction/models/gof_mip360_bonsai_crop_mesh_test"
DEFAULT_GOF_PYTHON="${HOME}/conda-envs/wind3dgs/gof/bin/python"

GPU="${GPU:-0}"
BASE_MODEL="${BASE_MODEL:-$DEFAULT_BASE_MODEL}"
CROP_ITERATION="${CROP_ITERATION:-crop}"
REFERENCE_ITERATION="${REFERENCE_ITERATION:-30000}"
OUTPUT_MODEL="${OUTPUT_MODEL:-$DEFAULT_OUTPUT_MODEL}"
OUTPUT_ITERATION="${OUTPUT_ITERATION:-30000}"
GOF_PYTHON="${GOF_PYTHON:-$DEFAULT_GOF_PYTHON}"
FILTER_MESH="${FILTER_MESH:-0}"
TEXTURE_MESH="${TEXTURE_MESH:-0}"
NEAR="${NEAR:-0.02}"
FAR="${FAR:-1000000}"
FORCE_PREPARE="${FORCE_PREPARE:-0}"
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
    --output-model)
      OUTPUT_MODEL="$2"
      shift 2
      ;;
    --output-iteration)
      OUTPUT_ITERATION="$2"
      shift 2
      ;;
    --gof-python)
      GOF_PYTHON="$2"
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
    --near)
      NEAR="$2"
      shift 2
      ;;
    --far)
      FAR="$2"
      shift 2
      ;;
    --force-prepare)
      FORCE_PREPARE=1
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
if [[ "$OUTPUT_MODEL" != /* ]]; then
  OUTPUT_MODEL="${PROJECT_ROOT}/${OUTPUT_MODEL}"
fi

RESTORE_SCRIPT="${SCRIPT_DIR}/restore_gof_filter3d_from_reference.py"
CROP_PLY="${BASE_MODEL}/point_cloud/iteration_${CROP_ITERATION}/point_cloud.ply"
REFERENCE_PLY="${BASE_MODEL}/point_cloud/iteration_${REFERENCE_ITERATION}/point_cloud.ply"
OUTPUT_PLY="${OUTPUT_MODEL}/point_cloud/iteration_${OUTPUT_ITERATION}/point_cloud.ply"
SUMMARY_PATH="${OUTPUT_MODEL}/point_cloud/iteration_${OUTPUT_ITERATION}/point_cloud.filter3d_summary.json"
LOG_DIR="${PROJECT_ROOT}/experiments/M04_mesh_extraction/outputs/logs"
LOG_FILE="${LOG_DIR}/bonsai_crop_mesh_extraction_$(date +%Y%m%d_%H%M%S).log"
MESH_PATH="${OUTPUT_MODEL}/test/ours_${OUTPUT_ITERATION}/fusion/mesh_binary_search_7.ply"

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

mesh_cmd=(
  "$GOF_PYTHON" extract_mesh.py
  -m "$OUTPUT_MODEL"
  --iteration "$OUTPUT_ITERATION"
  --near "$NEAR"
  --far "$FAR"
)
if [[ "$FILTER_MESH" == "1" ]]; then
  mesh_cmd+=(--filter_mesh)
fi
if [[ "$TEXTURE_MESH" == "1" ]]; then
  mesh_cmd+=(--texture_mesh)
fi

require_path "$RESTORE_SCRIPT" "filter_3D 복원 스크립트"
require_path "$GOF_DIR/extract_mesh.py" "GOF extract_mesh.py"
require_path "$GOF_PYTHON" "GOF Python"
require_path "$BASE_MODEL/cfg_args" "base cfg_args"
require_path "$BASE_MODEL/cameras.json" "base cameras.json"
require_path "$BASE_MODEL/input.ply" "base input.ply"
require_path "$CROP_PLY" "crop PLY"
require_path "$REFERENCE_PLY" "reference PLY"

if [[ "$DRY_RUN" == "1" ]]; then
  echo "== bonsai crop mesh extraction dry-run =="
  echo "project:             $PROJECT_ROOT"
  echo "base_model:          $BASE_MODEL"
  echo "crop_ply:            $CROP_PLY"
  echo "reference_ply:       $REFERENCE_PLY"
  echo "output_model:        $OUTPUT_MODEL"
  echo "output_ply:          $OUTPUT_PLY"
  echo "summary:             $SUMMARY_PATH"
  echo "mesh:                $MESH_PATH"
  echo "gof_dir:             $GOF_DIR"
  echo "python:              $GOF_PYTHON"
  echo "gpu:                 $GPU"
  echo "filter_mesh:         $FILTER_MESH"
  echo "texture_mesh:        $TEXTURE_MESH"
  echo "near/far:            $NEAR / $FAR"
  echo
  echo "mesh command:"
  print_cmd "${mesh_cmd[@]}"
  exit 0
fi

mkdir -p "$LOG_DIR" "$OUTPUT_MODEL" "$(dirname "$OUTPUT_PLY")" "$MPLCONFIGDIR"
exec > >(tee "$LOG_FILE") 2>&1

echo "== bonsai crop mesh extraction 테스트 =="
date '+시작: %Y-%m-%d %H:%M:%S %Z'
echo "project:             $PROJECT_ROOT"
echo "base_model:          $BASE_MODEL"
echo "crop_ply:            $CROP_PLY"
echo "reference_ply:       $REFERENCE_PLY"
echo "output_model:        $OUTPUT_MODEL"
echo "output_ply:          $OUTPUT_PLY"
echo "summary:             $SUMMARY_PATH"
echo "mesh:                $MESH_PATH"
echo "gof_dir:             $GOF_DIR"
echo "python:              $GOF_PYTHON"
echo "gpu:                 $GPU"
echo "omp threads:         $OMP_NUM_THREADS"
echo "mplconfigdir:        $MPLCONFIGDIR"
echo "filter_mesh:         $FILTER_MESH"
echo "texture_mesh:        $TEXTURE_MESH"
echo "near/far:            $NEAR / $FAR"
echo "log:                 $LOG_FILE"
echo

cp -f "$BASE_MODEL/cfg_args" "$OUTPUT_MODEL/cfg_args"
cp -f "$BASE_MODEL/cameras.json" "$OUTPUT_MODEL/cameras.json"
cp -f "$BASE_MODEL/input.ply" "$OUTPUT_MODEL/input.ply"

if [[ "$FORCE_PREPARE" == "1" || ! -f "$OUTPUT_PLY" ]]; then
  echo "crop PLY에 filter_3D를 복원한다."
  "$GOF_PYTHON" "$RESTORE_SCRIPT" \
    --input "$CROP_PLY" \
    --reference "$REFERENCE_PLY" \
    --output "$OUTPUT_PLY" \
    --summary "$SUMMARY_PATH"
else
  echo "복원된 crop PLY가 이미 있어서 재사용한다: $OUTPUT_PLY"
fi

echo
echo "복원 결과:"
stat -c '  point_cloud: %n %s bytes' "$OUTPUT_PLY"
if [[ -f "$SUMMARY_PATH" ]]; then
  sed -n '1,80p' "$SUMMARY_PATH"
fi

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

echo
echo "mesh extraction command:"
print_cmd "${mesh_cmd[@]}"
echo
echo "아래부터 GOF mesh extraction 출력이다."

set +e
(
  cd "$GOF_DIR"
  export CUDA_VISIBLE_DEVICES="$GPU"
  export OMP_NUM_THREADS="$OMP_NUM_THREADS"
  export MPLCONFIGDIR="$MPLCONFIGDIR"
  "${mesh_cmd[@]}"
)
mesh_status=$?
set -e

echo
date '+mesh extraction 종료: %Y-%m-%d %H:%M:%S %Z'
echo "mesh_exit_status: $mesh_status"
if [[ "$mesh_status" -ne 0 ]]; then
  exit "$mesh_status"
fi

if [[ -f "$MESH_PATH" ]]; then
  stat -c '  mesh: %n %s bytes' "$MESH_PATH"
else
  echo "mesh 파일이 없다: $MESH_PATH"
  exit 4
fi

echo
date '+종료: %Y-%m-%d %H:%M:%S %Z'
echo "status: OK"
echo "model_dir: $OUTPUT_MODEL"
echo "point_cloud: $OUTPUT_PLY"
echo "mesh: $MESH_PATH"
echo "log: $LOG_FILE"
