#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
압축 해제된 Mip-NeRF 360 scene에서 작은 GOF/3DGS 스모크 학습을 실행한다.

사용법:
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh [scene]
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke.sh --scene flowers --iterations 1000 --images images_4

기본값:
  scene:       bonsai
  iterations: 1000
  images:     images_4
  output:     experiments/M04_mesh_extraction/models/gof_mip360_<scene>_i<iterations>_<images>

옵션:
  -s, --scene NAME          raw/mipnerf360 아래 scene 이름. bonsai, flowers, garden, stump, treehill 중 하나.
  -n, --iterations N        스모크 테스트 학습 iteration 수.
  -i, --images DIR          scene 내부 이미지 폴더. 예: images_4, images_2.
  -m, --model-dir DIR       출력 model 디렉터리. 상대 경로는 project root 기준으로 해석한다.
      --gpu ID              CUDA_VISIBLE_DEVICES 값. 기본값: 0.
      --port PORT           GOF viewer/server port 인자. 기본값: 6009.
      --data-device DEVICE  GOF data_device 인자. 기본값: cpu.
      --run-render          학습 후 train view render를 실행한다.
      --run-mesh            학습 후 GOF extract_mesh.py를 실행한다.
      --skip-train-if-ready 해당 iteration의 point_cloud가 이미 있으면 학습을 건너뛰고 요청한 후처리만 실행한다.
      --backup-existing     model 디렉터리가 이미 있으면 timestamp suffix를 붙여 백업한다.
      --dry-run             학습 없이 경로를 검증하고 실행 command만 출력한다.
  -h, --help                이 도움말을 출력한다.

환경 변수 override:
  GOF_PYTHON=/path/to/python
  OMP_NUM_THREADS=4
  MPLCONFIGDIR=/tmp/mpl-gof
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
GOF_DIR="${PROJECT_ROOT}/external/gaussian-opacity-fields"
DEFAULT_GOF_PYTHON="${HOME}/conda-envs/wind3dgs/gof/bin/python"

SCENE="${SCENE:-bonsai}"
ITERATIONS="${ITERATIONS:-1000}"
IMAGE_DIR="${IMAGE_DIR:-images_4}"
MODEL_DIR="${MODEL_DIR:-}"
GPU="${GPU:-0}"
PORT="${PORT:-6009}"
DATA_DEVICE="${DATA_DEVICE:-cpu}"
RUN_RENDER="${RUN_RENDER:-0}"
RUN_MESH="${RUN_MESH:-0}"
SKIP_TRAIN_IF_READY="${SKIP_TRAIN_IF_READY:-0}"
BACKUP_EXISTING="${BACKUP_EXISTING:-0}"
DRY_RUN="${DRY_RUN:-0}"
GOF_PYTHON="${GOF_PYTHON:-$DEFAULT_GOF_PYTHON}"
OMP_NUM_THREADS="${OMP_NUM_THREADS:-4}"
MPLCONFIGDIR="${MPLCONFIGDIR:-/tmp/mpl-gof}"

POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    -s|--scene)
      SCENE="$2"
      shift 2
      ;;
    -n|--iterations)
      ITERATIONS="$2"
      shift 2
      ;;
    -i|--images)
      IMAGE_DIR="$2"
      shift 2
      ;;
    -m|--model-dir)
      MODEL_DIR="$2"
      shift 2
      ;;
    --gpu)
      GPU="$2"
      shift 2
      ;;
    --port)
      PORT="$2"
      shift 2
      ;;
    --data-device)
      DATA_DEVICE="$2"
      shift 2
      ;;
    --run-render)
      RUN_RENDER=1
      shift
      ;;
    --run-mesh)
      RUN_MESH=1
      shift
      ;;
    --skip-train-if-ready)
      SKIP_TRAIN_IF_READY=1
      shift
      ;;
    --backup-existing)
      BACKUP_EXISTING=1
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
    --)
      shift
      while [[ $# -gt 0 ]]; do
        POSITIONAL+=("$1")
        shift
      done
      ;;
    -*)
      echo "알 수 없는 옵션: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done

if [[ "${#POSITIONAL[@]}" -gt 0 ]]; then
  SCENE="${POSITIONAL[0]}"
fi
if [[ "${#POSITIONAL[@]}" -gt 1 ]]; then
  ITERATIONS="${POSITIONAL[1]}"
fi
if [[ "${#POSITIONAL[@]}" -gt 2 ]]; then
  IMAGE_DIR="${POSITIONAL[2]}"
fi
if [[ "${#POSITIONAL[@]}" -gt 3 ]]; then
  echo "위치 인자가 너무 많다: ${POSITIONAL[*]}" >&2
  usage >&2
  exit 2
fi

if [[ ! "$ITERATIONS" =~ ^[0-9]+$ ]]; then
  echo "iterations는 양의 정수여야 한다: $ITERATIONS" >&2
  exit 2
fi

case "$SCENE" in
  bonsai|flowers|garden|stump|treehill)
    ;;
  *)
    echo "알 수 없거나 지원하지 않는 Mip-NeRF 360 scene: $SCENE" >&2
    echo "가능한 값: bonsai flowers garden stump treehill" >&2
    exit 2
    ;;
esac

SOURCE_DIR="${PROJECT_ROOT}/experiments/M04_mesh_extraction/raw/mipnerf360/${SCENE}"
if [[ -z "$MODEL_DIR" ]]; then
  MODEL_DIR="${PROJECT_ROOT}/experiments/M04_mesh_extraction/models/gof_mip360_${SCENE}_i${ITERATIONS}_${IMAGE_DIR}"
elif [[ "$MODEL_DIR" != /* ]]; then
  MODEL_DIR="${PROJECT_ROOT}/${MODEL_DIR}"
fi

LOG_DIR="${PROJECT_ROOT}/experiments/M04_mesh_extraction/outputs/logs"
LOG_FILE="${LOG_DIR}/gof_mip360_${SCENE}_i${ITERATIONS}_${IMAGE_DIR}_$(date +%Y%m%d_%H%M%S).log"
LOCKDIR="${MODEL_DIR}.lock"
PLY_PATH="${MODEL_DIR}/point_cloud/iteration_${ITERATIONS}/point_cloud.ply"
MESH_PATH="${MODEL_DIR}/test/ours_${ITERATIONS}/fusion/mesh_binary_search_7.ply"

require_path() {
  local path="$1"
  local label="$2"
  if [[ ! -e "$path" ]]; then
    echo "${label} 경로가 없다: ${path}" >&2
    exit 1
  fi
}

require_path "$GOF_DIR/train.py" "GOF train.py"
require_path "$GOF_DIR/extract_mesh.py" "GOF extract_mesh.py"
require_path "$GOF_PYTHON" "GOF Python"
require_path "$SOURCE_DIR" "scene directory"
require_path "$SOURCE_DIR/$IMAGE_DIR" "image directory"
require_path "$SOURCE_DIR/sparse/0/cameras.bin" "COLMAP cameras.bin"
require_path "$SOURCE_DIR/sparse/0/images.bin" "COLMAP images.bin"
require_path "$SOURCE_DIR/sparse/0/points3D.bin" "COLMAP points3D.bin"

MODEL_READY=0
if [[ -d "$MODEL_DIR" ]] && [[ -n "$(find "$MODEL_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  if [[ "$SKIP_TRAIN_IF_READY" == "1" && -f "$PLY_PATH" ]]; then
    MODEL_READY=1
  elif [[ "$BACKUP_EXISTING" == "1" ]]; then
    BACKUP_DIR="${MODEL_DIR}.bak_$(date +%Y%m%d_%H%M%S)"
    mv "$MODEL_DIR" "$BACKUP_DIR"
    echo "기존 model 디렉터리를 백업했다: $BACKUP_DIR"
  else
    echo "model 디렉터리가 이미 있고 비어 있지 않다:" >&2
    echo "  $MODEL_DIR" >&2
    echo "새 --model-dir를 지정하거나 --backup-existing으로 다시 실행해라." >&2
    exit 1
  fi
fi

train_cmd=(
  "$GOF_PYTHON" train.py
  -s "$SOURCE_DIR"
  -m "$MODEL_DIR"
  --eval
  -i "$IMAGE_DIR"
  --iterations "$ITERATIONS"
  --test_iterations "$ITERATIONS"
  --save_iterations "$ITERATIONS"
  --data_device "$DATA_DEVICE"
  --port "$PORT"
)

render_cmd=(
  "$GOF_PYTHON" render.py
  -m "$MODEL_DIR"
  --iteration "$ITERATIONS"
  --skip_test
  --data_device "$DATA_DEVICE"
)

mesh_cmd=(
  "$GOF_PYTHON" extract_mesh.py
  -m "$MODEL_DIR"
  --iteration "$ITERATIONS"
)

print_cmd() {
  printf '  '
  printf '%q ' "$@"
  printf '\n'
}

if [[ "$DRY_RUN" == "1" ]]; then
  echo "== GOF Mip-NeRF 360 스모크 dry-run =="
  echo "project:       $PROJECT_ROOT"
  echo "scene:         $SCENE"
  echo "source:        $SOURCE_DIR"
  echo "images:        $IMAGE_DIR"
  echo "iterations:    $ITERATIONS"
  echo "model:         $MODEL_DIR"
  echo "gof dir:       $GOF_DIR"
  echo "python:        $GOF_PYTHON"
  echo "gpu:           $GPU"
  echo "data_device:   $DATA_DEVICE"
  echo "model 준비됨:  $MODEL_READY"
  echo "준비 시 skip:  $SKIP_TRAIN_IF_READY"
  echo
  echo "학습 command:"
  print_cmd "${train_cmd[@]}"
  if [[ "$RUN_RENDER" == "1" ]]; then
    echo
    echo "render command:"
    print_cmd "${render_cmd[@]}"
  fi
  if [[ "$RUN_MESH" == "1" ]]; then
    echo
    echo "mesh extraction command:"
    print_cmd "${mesh_cmd[@]}"
  fi
  echo
  echo "dry_run: OK"
  exit 0
fi

if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "다른 GOF 스모크 실행이 살아 있을 수 있다: $LOCKDIR" >&2
  echo "stale lock이 확실하면 다음 명령으로 지워라:" >&2
  echo "  rmdir '$LOCKDIR'" >&2
  exit 1
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null || true' EXIT

mkdir -p "$LOG_DIR" "$MODEL_DIR" "$MPLCONFIGDIR"

{
  echo "== GOF Mip-NeRF 360 스모크 학습 =="
  date '+시작: %Y-%m-%d %H:%M:%S %Z'
  echo "project:        $PROJECT_ROOT"
  echo "scene:          $SCENE"
  echo "source:         $SOURCE_DIR"
  echo "images:         $IMAGE_DIR"
  echo "iterations:     $ITERATIONS"
  echo "model:          $MODEL_DIR"
  echo "gof dir:        $GOF_DIR"
  echo "python:         $GOF_PYTHON"
  echo "gpu:            $GPU"
  echo "data_device:    $DATA_DEVICE"
  echo "omp threads:    $OMP_NUM_THREADS"
  echo "mplconfigdir:   $MPLCONFIGDIR"
  echo "model 준비됨:   $MODEL_READY"
  echo "준비 시 skip:   $SKIP_TRAIN_IF_READY"
  echo "log:            $LOG_FILE"
  echo
  echo "입력 파일 수:"
  printf '  %s 파일: ' "$IMAGE_DIR"
  find "$SOURCE_DIR/$IMAGE_DIR" -maxdepth 1 -type f | wc -l
  printf '  sparse 파일: '
  find "$SOURCE_DIR/sparse/0" -maxdepth 1 -type f | wc -l
  echo
  if [[ "$MODEL_READY" == "1" && "$RUN_RENDER" != "1" && "$RUN_MESH" != "1" ]]; then
    echo "GPU 사전 확인: model이 이미 준비됐고 요청된 후처리가 없어 건너뛴다."
  else
    echo "GPU 사전 확인:"
  fi
} | tee "$LOG_FILE"

if [[ "$MODEL_READY" != "1" || "$RUN_RENDER" == "1" || "$RUN_MESH" == "1" ]]; then
  set +e
  CUDA_VISIBLE_DEVICES="$GPU" "$GOF_PYTHON" - <<'PY' 2>&1 | tee -a "$LOG_FILE"
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
  preflight_status=${PIPESTATUS[0]}
  set -e

  if [[ "$preflight_status" -ne 0 ]]; then
    {
      echo
      echo "GPU 사전 확인 실패 status: $preflight_status"
      echo "같은 터미널에서 WSL GPU 접근을 확인한 뒤 이 스크립트를 다시 실행해라."
    } | tee -a "$LOG_FILE"
    exit "$preflight_status"
  fi
fi

if [[ "$MODEL_READY" == "1" ]]; then
  {
    echo
    echo "point cloud가 이미 있어서 학습을 건너뛴다:"
    echo "  $PLY_PATH"
  } | tee -a "$LOG_FILE"
else
  {
    echo
    echo "학습 command:"
    print_cmd "${train_cmd[@]}"
    echo
    echo "아래부터 GOF 학습 출력이다."
    echo
  } | tee -a "$LOG_FILE"

  set +e
  (
    cd "$GOF_DIR"
    export CUDA_VISIBLE_DEVICES="$GPU"
    export OMP_NUM_THREADS="$OMP_NUM_THREADS"
    export MPLCONFIGDIR="$MPLCONFIGDIR"
    "${train_cmd[@]}"
  ) 2>&1 | tee -a "$LOG_FILE"
  train_status=${PIPESTATUS[0]}
  set -e

  {
    echo
    date '+학습 종료: %Y-%m-%d %H:%M:%S %Z'
    echo "학습 exit status: $train_status"
  } | tee -a "$LOG_FILE"

  if [[ "$train_status" -ne 0 ]]; then
    exit "$train_status"
  fi
fi

{
  echo
  echo "스모크 학습 산출물 확인:"
  if [[ -f "$PLY_PATH" ]]; then
    stat -c '  point_cloud: %n %s bytes' "$PLY_PATH"
  else
    echo "  point_cloud가 없다: $PLY_PATH"
    exit 4
  fi
} | tee -a "$LOG_FILE"

if [[ "$RUN_RENDER" == "1" ]]; then
  {
    echo
    echo "render command:"
    print_cmd "${render_cmd[@]}"
    echo
  } | tee -a "$LOG_FILE"
  set +e
  (
    cd "$GOF_DIR"
    export CUDA_VISIBLE_DEVICES="$GPU"
    export OMP_NUM_THREADS="$OMP_NUM_THREADS"
    export MPLCONFIGDIR="$MPLCONFIGDIR"
    "${render_cmd[@]}"
  ) 2>&1 | tee -a "$LOG_FILE"
  render_status=${PIPESTATUS[0]}
  set -e
  echo "render_exit_status: $render_status" | tee -a "$LOG_FILE"
  if [[ "$render_status" -ne 0 ]]; then
    exit "$render_status"
  fi
fi

if [[ "$RUN_MESH" == "1" ]]; then
  {
    echo
    echo "mesh extraction command:"
    print_cmd "${mesh_cmd[@]}"
    echo
  } | tee -a "$LOG_FILE"
  set +e
  (
    cd "$GOF_DIR"
    export CUDA_VISIBLE_DEVICES="$GPU"
    export OMP_NUM_THREADS="$OMP_NUM_THREADS"
    export MPLCONFIGDIR="$MPLCONFIGDIR"
    "${mesh_cmd[@]}"
  ) 2>&1 | tee -a "$LOG_FILE"
  mesh_status=${PIPESTATUS[0]}
  set -e
  echo "mesh_exit_status: $mesh_status" | tee -a "$LOG_FILE"
  if [[ "$mesh_status" -ne 0 ]]; then
    exit "$mesh_status"
  fi
  if [[ -f "$MESH_PATH" ]]; then
    stat -c '  mesh: %n %s bytes' "$MESH_PATH" | tee -a "$LOG_FILE"
  fi
fi

{
  echo
  date '+종료: %Y-%m-%d %H:%M:%S %Z'
  echo "status: OK"
  echo "model_dir: $MODEL_DIR"
  echo "point_cloud: $PLY_PATH"
  if [[ "$RUN_MESH" == "1" ]]; then
    echo "mesh: $MESH_PATH"
  fi
  echo "log: $LOG_FILE"
} | tee -a "$LOG_FILE"
