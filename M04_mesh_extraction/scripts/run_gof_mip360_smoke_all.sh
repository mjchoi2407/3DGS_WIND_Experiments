#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
준비된 Mip-NeRF 360 scene 전체에 대해 GOF/3DGS 스모크 학습을 순차 실행한다.

사용법:
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --iterations 1000 --images images_4
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_smoke_all.sh --scenes "bonsai flowers" --run-mesh

기본값:
  scenes:      bonsai flowers garden stump treehill
  iterations: 1000
  images:     images_4
  gpu:        0
  port-start: 6009

옵션:
      --scenes LIST         실행할 scene 목록. 따옴표로 감싼 공백 구분 문자열을 권장한다.
  -n, --iterations N        각 scene의 스모크 테스트 학습 iteration 수.
  -i, --images DIR          모든 scene에 사용할 이미지 폴더. 예: images_4, images_2.
      --official-factors    GOF 공식 Mip-NeRF 360 factor를 사용한다. 현재 보유 scene 기준 bonsai=images_2, 나머지=images_4.
      --gpu ID              CUDA_VISIBLE_DEVICES 값. 기본값: 0.
      --port-start PORT     scene별 port 시작값. scene마다 1씩 증가한다.
      --data-device DEVICE  GOF data_device 인자. 기본값: cpu.
      --run-render          각 scene 학습 후 train view render를 실행한다.
      --run-mesh            각 scene 학습 후 GOF extract_mesh.py를 실행한다.
      --skip-train-if-ready 이미 point_cloud가 있으면 해당 scene 학습을 건너뛰고 요청한 후처리만 실행한다.
      --backup-existing     기존 model 디렉터리가 있으면 timestamp suffix를 붙여 백업한다.
      --continue-on-error   한 scene이 실패해도 다음 scene을 계속 실행한다.
      --dry-run             학습 없이 전체 실행 계획과 scene별 command만 출력한다.
  -h, --help                이 도움말을 출력한다.

환경 변수 override:
  SCENES="bonsai flowers garden stump treehill"
  ITERATIONS=1000
  IMAGE_DIR=images_4
  GPU=0
  PORT_START=6009
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SINGLE_SCRIPT="${SCRIPT_DIR}/run_gof_mip360_smoke.sh"

SCENES_RAW="${SCENES:-bonsai flowers garden stump treehill}"
ITERATIONS="${ITERATIONS:-1000}"
IMAGE_DIR="${IMAGE_DIR:-images_4}"
GPU="${GPU:-0}"
PORT_START="${PORT_START:-6009}"
DATA_DEVICE="${DATA_DEVICE:-cpu}"
OFFICIAL_FACTORS="${OFFICIAL_FACTORS:-0}"
RUN_RENDER="${RUN_RENDER:-0}"
RUN_MESH="${RUN_MESH:-0}"
SKIP_TRAIN_IF_READY="${SKIP_TRAIN_IF_READY:-0}"
BACKUP_EXISTING="${BACKUP_EXISTING:-0}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-0}"
DRY_RUN="${DRY_RUN:-0}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenes)
      SCENES_RAW="$2"
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
    --official-factors)
      OFFICIAL_FACTORS=1
      shift
      ;;
    --gpu)
      GPU="$2"
      shift 2
      ;;
    --port-start)
      PORT_START="$2"
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
    --continue-on-error)
      CONTINUE_ON_ERROR=1
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
      if [[ $# -gt 0 ]]; then
        SCENES_RAW="$*"
      fi
      break
      ;;
    -*)
      echo "알 수 없는 옵션: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      SCENES_RAW="$*"
      break
      ;;
  esac
done

read -r -a SCENES <<< "$SCENES_RAW"

if [[ "${#SCENES[@]}" -eq 0 ]]; then
  echo "실행할 scene이 없다." >&2
  exit 2
fi
if [[ ! "$ITERATIONS" =~ ^[0-9]+$ ]]; then
  echo "iterations는 양의 정수여야 한다: $ITERATIONS" >&2
  exit 2
fi
if [[ ! "$PORT_START" =~ ^[0-9]+$ ]]; then
  echo "port-start는 양의 정수여야 한다: $PORT_START" >&2
  exit 2
fi
if [[ ! -x "$SINGLE_SCRIPT" ]]; then
  echo "단일 scene 스모크 스크립트를 실행할 수 없다: $SINGLE_SCRIPT" >&2
  exit 1
fi

scene_image_dir() {
  local scene="$1"
  if [[ "$OFFICIAL_FACTORS" == "1" ]]; then
    case "$scene" in
      bonsai) echo "images_2" ;;
      flowers|garden|stump|treehill) echo "images_4" ;;
      *) echo "$IMAGE_DIR" ;;
    esac
  else
    echo "$IMAGE_DIR"
  fi
}

check_scene_name() {
  local scene="$1"
  case "$scene" in
    bonsai|flowers|garden|stump|treehill)
      ;;
    *)
      echo "알 수 없거나 지원하지 않는 Mip-NeRF 360 scene: $scene" >&2
      echo "가능한 값: bonsai flowers garden stump treehill" >&2
      exit 2
      ;;
  esac
}

model_dir_for() {
  local scene="$1"
  local image_dir="$2"
  echo "${PROJECT_ROOT}/experiments/M04_mesh_extraction/models/gof_mip360_${scene}_i${ITERATIONS}_${image_dir}"
}

print_cmd() {
  printf '  '
  printf '%q ' "$@"
  printf '\n'
}

write_plan_block() {
  local target="$1"
  local mode="$2"
  if [[ "$target" == "/dev/stdout" ]]; then
    cat
  elif [[ "$mode" == "append" ]]; then
    tee -a "$target"
  else
    tee "$target"
  fi
}

for scene in "${SCENES[@]}"; do
  check_scene_name "$scene"
  image_dir="$(scene_image_dir "$scene")"
  source_dir="${PROJECT_ROOT}/experiments/M04_mesh_extraction/raw/mipnerf360/${scene}"
  if [[ ! -d "$source_dir" ]]; then
    echo "scene 디렉터리가 없다: $source_dir" >&2
    exit 1
  fi
  if [[ ! -d "${source_dir}/${image_dir}" ]]; then
    echo "이미지 디렉터리가 없다: ${source_dir}/${image_dir}" >&2
    exit 1
  fi
  if [[ ! -f "${source_dir}/sparse/0/cameras.bin" || ! -f "${source_dir}/sparse/0/images.bin" || ! -f "${source_dir}/sparse/0/points3D.bin" ]]; then
    echo "COLMAP sparse 파일이 부족하다: ${source_dir}/sparse/0" >&2
    exit 1
  fi
done

LOG_DIR="${PROJECT_ROOT}/experiments/M04_mesh_extraction/outputs/logs"
BATCH_STAMP="$(date +%Y%m%d_%H%M%S)"
IMAGE_TAG="$IMAGE_DIR"
if [[ "$OFFICIAL_FACTORS" == "1" ]]; then
  IMAGE_TAG="official_factors"
fi
BATCH_LOG="${LOG_DIR}/gof_mip360_all_i${ITERATIONS}_${IMAGE_TAG}_${BATCH_STAMP}.log"

if [[ "$DRY_RUN" != "1" ]]; then
  mkdir -p "$LOG_DIR"
fi

build_scene_cmd() {
  local scene="$1"
  local image_dir="$2"
  local port="$3"
  local -n out_cmd="$4"

  out_cmd=(
    "$SINGLE_SCRIPT"
    --scene "$scene"
    --iterations "$ITERATIONS"
    --images "$image_dir"
    --gpu "$GPU"
    --port "$port"
    --data-device "$DATA_DEVICE"
  )
  if [[ "$RUN_RENDER" == "1" ]]; then
    out_cmd+=(--run-render)
  fi
  if [[ "$RUN_MESH" == "1" ]]; then
    out_cmd+=(--run-mesh)
  fi
  if [[ "$SKIP_TRAIN_IF_READY" == "1" ]]; then
    out_cmd+=(--skip-train-if-ready)
  fi
  if [[ "$BACKUP_EXISTING" == "1" ]]; then
    out_cmd+=(--backup-existing)
  fi
  if [[ "$DRY_RUN" == "1" ]]; then
    out_cmd+=(--dry-run)
  fi
}

print_plan() {
  local output_target="$1"
  {
    echo "== GOF Mip-NeRF 360 전체 스모크 계획 =="
    date '+생성: %Y-%m-%d %H:%M:%S %Z'
    echo "project:          $PROJECT_ROOT"
    echo "scene 수:         ${#SCENES[@]}"
    echo "scenes:           ${SCENES[*]}"
    echo "iterations:       $ITERATIONS"
    echo "images:           $IMAGE_TAG"
    echo "gpu:              $GPU"
    echo "port 시작값:      $PORT_START"
    echo "data_device:      $DATA_DEVICE"
    echo "run_render:       $RUN_RENDER"
    echo "run_mesh:         $RUN_MESH"
    echo "skip_ready:       $SKIP_TRAIN_IF_READY"
    echo "backup_existing:  $BACKUP_EXISTING"
    echo "continue_error:   $CONTINUE_ON_ERROR"
    echo "batch log:        $BATCH_LOG"
    echo
    echo "scene별 command:"
  } | write_plan_block "$output_target" "write"

  local idx=0
  for scene in "${SCENES[@]}"; do
    idx=$((idx + 1))
    image_dir="$(scene_image_dir "$scene")"
    port=$((PORT_START + idx - 1))
    local cmd=()
    build_scene_cmd "$scene" "$image_dir" "$port" cmd
    {
      printf '\n[%d/%d] %s / %s / port=%s\n' "$idx" "${#SCENES[@]}" "$scene" "$image_dir" "$port"
      print_cmd "${cmd[@]}"
    } | write_plan_block "$output_target" "append"
  done
}

if [[ "$DRY_RUN" == "1" ]]; then
  print_plan /dev/stdout
  echo
  echo "dry_run: OK"
  exit 0
fi

print_plan "$BATCH_LOG"

batch_start_epoch="$(date +%s)"
declare -a SUMMARY=()
overall_status=0

idx=0
for scene in "${SCENES[@]}"; do
  idx=$((idx + 1))
  image_dir="$(scene_image_dir "$scene")"
  port=$((PORT_START + idx - 1))
  percent=$((idx * 100 / ${#SCENES[@]}))
  scene_start_epoch="$(date +%s)"
  model_dir="$(model_dir_for "$scene" "$image_dir")"
  ply_path="${model_dir}/point_cloud/iteration_${ITERATIONS}/point_cloud.ply"
  mesh_path="${model_dir}/test/ours_${ITERATIONS}/fusion/mesh_binary_search_7.ply"
  cmd=()
  build_scene_cmd "$scene" "$image_dir" "$port" cmd

  {
    echo
    echo "================================================================"
    printf '전체 진행: [%d/%d] %d%% | scene=%s | images=%s\n' "$idx" "${#SCENES[@]}" "$percent" "$scene" "$image_dir"
    date '+scene 시작: %Y-%m-%d %H:%M:%S %Z'
    echo "model: $model_dir"
    echo "command:"
    print_cmd "${cmd[@]}"
    echo "----------------------------------------------------------------"
  } | tee -a "$BATCH_LOG"

  set +e
  "${cmd[@]}" 2>&1 | tee -a "$BATCH_LOG"
  status=${PIPESTATUS[0]}
  set -e

  scene_end_epoch="$(date +%s)"
  scene_elapsed=$((scene_end_epoch - scene_start_epoch))
  batch_elapsed=$((scene_end_epoch - batch_start_epoch))

  if [[ "$status" -eq 0 ]]; then
    ply_status="missing"
    mesh_status="not_requested"
    if [[ -f "$ply_path" ]]; then
      ply_status="ok"
    fi
    if [[ "$RUN_MESH" == "1" ]]; then
      if [[ -f "$mesh_path" ]]; then
        mesh_status="ok"
      else
        mesh_status="missing"
      fi
    fi
    SUMMARY+=("OK | ${scene} | ${image_dir} | ${scene_elapsed}s | point_cloud=${ply_status} | mesh=${mesh_status}")
  else
    SUMMARY+=("FAIL(${status}) | ${scene} | ${image_dir} | ${scene_elapsed}s")
    overall_status="$status"
  fi

  {
    echo "----------------------------------------------------------------"
    date '+scene 종료: %Y-%m-%d %H:%M:%S %Z'
    echo "scene exit status: $status"
    echo "scene 소요 시간: ${scene_elapsed}s"
    echo "batch 누적 시간: ${batch_elapsed}s"
    echo "현재까지 요약:"
    for item in "${SUMMARY[@]}"; do
      echo "  - $item"
    done
  } | tee -a "$BATCH_LOG"

  if [[ "$status" -ne 0 && "$CONTINUE_ON_ERROR" != "1" ]]; then
    {
      echo
      echo "실패한 scene이 있어 batch를 중단한다. 계속 진행하려면 --continue-on-error를 사용해라."
    } | tee -a "$BATCH_LOG"
    break
  fi
done

{
  echo
  echo "================================================================"
  echo "전체 스모크 batch 요약"
  date '+종료: %Y-%m-%d %H:%M:%S %Z'
  echo "전체 소요 시간: $(( $(date +%s) - batch_start_epoch ))s"
  echo "batch log: $BATCH_LOG"
  for item in "${SUMMARY[@]}"; do
    echo "  - $item"
  done
  if [[ "$overall_status" -eq 0 ]]; then
    echo "status: OK"
  else
    echo "status: FAIL(${overall_status})"
  fi
} | tee -a "$BATCH_LOG"

exit "$overall_status"
