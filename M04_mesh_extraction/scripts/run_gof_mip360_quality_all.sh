#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
준비된 Mip-NeRF 360 scene 전체에 대해 연구용 고퀄 GOF/3DGS 학습, SIBR 호환 변환,
render를 순차 실행한다.

사용법:
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh --scenes "bonsai flowers"
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_quality_all.sh --iterations 30000 --official-factors

기본값:
  scenes:      bonsai flowers garden stump treehill
  iterations: 30000
  images:     official factors, bonsai=images_2, 나머지=images_4
  gpu:        0
  port-start: 6109
  render:     켬
  convert:    켬, iteration_sibr_safe/point_cloud.ply 생성

옵션:
      --scenes LIST          실행할 scene 목록. 따옴표로 감싼 공백 구분 문자열을 권장한다.
  -n, --iterations N         각 scene의 학습 iteration 수. 기본값: 30000.
  -i, --images DIR           모든 scene에 사용할 이미지 폴더. 지정하면 official factors를 끈다.
      --official-factors     현재 보유 scene 기준 bonsai=images_2, 나머지=images_4를 사용한다.
      --no-official-factors  모든 scene에 --images 값을 사용한다.
      --gpu ID               CUDA_VISIBLE_DEVICES 값. 기본값: 0.
      --port-start PORT      scene별 port 시작값. scene마다 1씩 증가한다.
      --data-device DEVICE   GOF data_device 인자. 기본값: cpu.
      --run-render           학습 후 train view render를 실행한다. 기본값: 켬.
      --no-render            render 단계를 건너뛴다.
      --convert              SIBR 호환 PLY 변환을 실행한다. 기본값: 켬.
      --no-convert           SIBR 호환 PLY 변환을 건너뛴다.
      --max-radius VALUE     viewer-safe 변환의 최대 반경. 기본값: 12.
      --max-scale VALUE      viewer-safe 변환의 최대 Gaussian scale. 기본값: 1.0.
      --min-opacity VALUE    viewer-safe 변환의 최소 opacity. 기본값: 0.0.
      --viewer-python PATH   변환 모듈 실행에 사용할 Python. 기본값: .venv/bin/python.
      --skip-train-if-ready  이미 point_cloud가 있으면 학습을 건너뛰고 변환/후처리만 실행한다.
      --backup-existing      기존 model 디렉터리가 있으면 timestamp suffix를 붙여 백업한다.
      --continue-on-error    한 scene이 실패해도 다음 scene을 계속 실행한다.
      --dry-run              학습 없이 전체 실행 계획과 scene별 command만 출력한다.
  -h, --help                 이 도움말을 출력한다.

환경 변수 override:
  SCENES="bonsai flowers garden stump treehill"
  ITERATIONS=30000
  IMAGE_DIR=images_4
  OFFICIAL_FACTORS=1
  GPU=0
  PORT_START=6109
  VIEWER_PYTHON=.venv/bin/python
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SINGLE_SCRIPT="${SCRIPT_DIR}/run_gof_mip360_smoke.sh"
FILTER_MODULE="wind3dgs.m04_mesh_extraction.filter_viewer_safe_ply"
DEFAULT_VIEWER_PYTHON="${PROJECT_ROOT}/.venv/bin/python"

SCENES_RAW="${SCENES:-bonsai flowers garden stump treehill}"
ITERATIONS="${ITERATIONS:-30000}"
IMAGE_DIR="${IMAGE_DIR:-images_4}"
OFFICIAL_FACTORS="${OFFICIAL_FACTORS:-1}"
GPU="${GPU:-0}"
PORT_START="${PORT_START:-6109}"
DATA_DEVICE="${DATA_DEVICE:-cpu}"
RUN_RENDER="${RUN_RENDER:-1}"
RUN_CONVERT="${RUN_CONVERT:-1}"
SKIP_TRAIN_IF_READY="${SKIP_TRAIN_IF_READY:-0}"
BACKUP_EXISTING="${BACKUP_EXISTING:-0}"
CONTINUE_ON_ERROR="${CONTINUE_ON_ERROR:-0}"
DRY_RUN="${DRY_RUN:-0}"
CONVERT_MAX_RADIUS="${CONVERT_MAX_RADIUS:-12}"
CONVERT_MAX_SCALE="${CONVERT_MAX_SCALE:-1.0}"
CONVERT_MIN_OPACITY="${CONVERT_MIN_OPACITY:-0.0}"
VIEWER_PYTHON="${VIEWER_PYTHON:-$DEFAULT_VIEWER_PYTHON}"

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
      OFFICIAL_FACTORS=0
      shift 2
      ;;
    --official-factors)
      OFFICIAL_FACTORS=1
      shift
      ;;
    --no-official-factors)
      OFFICIAL_FACTORS=0
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
    --no-render)
      RUN_RENDER=0
      shift
      ;;
    --convert)
      RUN_CONVERT=1
      shift
      ;;
    --no-convert)
      RUN_CONVERT=0
      shift
      ;;
    --max-radius)
      CONVERT_MAX_RADIUS="$2"
      shift 2
      ;;
    --max-scale)
      CONVERT_MAX_SCALE="$2"
      shift 2
      ;;
    --min-opacity)
      CONVERT_MIN_OPACITY="$2"
      shift 2
      ;;
    --viewer-python)
      VIEWER_PYTHON="$2"
      shift 2
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
  echo "단일 scene 학습 스크립트를 실행할 수 없다: $SINGLE_SCRIPT" >&2
  exit 1
fi
if [[ "$RUN_CONVERT" == "1" && ! -x "$VIEWER_PYTHON" ]]; then
  echo "변환용 Python을 실행할 수 없다: $VIEWER_PYTHON" >&2
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

point_cloud_for() {
  local model_dir="$1"
  echo "${model_dir}/point_cloud/iteration_${ITERATIONS}/point_cloud.ply"
}

sibr_point_cloud_for() {
  local model_dir="$1"
  echo "${model_dir}/point_cloud/iteration_sibr_safe/point_cloud.ply"
}

print_cmd() {
  printf '  '
  printf '%q ' "$@"
  printf '\n'
}

write_block() {
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

build_train_cmd() {
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

build_post_cmd() {
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
    --skip-train-if-ready
  )
  if [[ "$RUN_RENDER" == "1" ]]; then
    out_cmd+=(--run-render)
  fi
  if [[ "$DRY_RUN" == "1" ]]; then
    out_cmd+=(--dry-run)
  fi
}

build_convert_cmd() {
  local input_ply="$1"
  local output_ply="$2"
  local -n out_cmd="$3"

  out_cmd=(
    "$VIEWER_PYTHON" -m "$FILTER_MODULE"
    --input "$input_ply"
    --output "$output_ply"
    --max-radius "$CONVERT_MAX_RADIUS"
    --max-scale "$CONVERT_MAX_SCALE"
    --min-opacity "$CONVERT_MIN_OPACITY"
    --sibr-compatible
  )
}

build_viewer_cmd() {
  local model_dir="$1"
  local scene="$2"
  local -n out_cmd="$3"

  out_cmd=(
    env SIBR_DEFAULT_ITERATION=sibr_safe
    "${PROJECT_ROOT}/code/scripts/run_sibr_gaussian_viewer.sh"
    "$model_dir"
    "${PROJECT_ROOT}/experiments/M04_mesh_extraction/raw/mipnerf360/${scene}"
  )
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
BATCH_LOG="${LOG_DIR}/gof_mip360_quality_i${ITERATIONS}_${IMAGE_TAG}_${BATCH_STAMP}.log"

if [[ "$DRY_RUN" != "1" ]]; then
  mkdir -p "$LOG_DIR"
fi

print_plan() {
  local output_target="$1"
  {
    echo "== GOF Mip-NeRF 360 연구용 고퀄 batch 계획 =="
    date '+생성: %Y-%m-%d %H:%M:%S %Z'
    echo "project:          $PROJECT_ROOT"
    echo "scene 수:         ${#SCENES[@]}"
    echo "scenes:           ${SCENES[*]}"
    echo "iterations:       $ITERATIONS"
    echo "images:           $IMAGE_TAG"
    echo "gpu:              $GPU"
    echo "port 시작값:      $PORT_START"
    echo "data_device:      $DATA_DEVICE"
    echo "run_convert:      $RUN_CONVERT"
    echo "run_render:       $RUN_RENDER"
    echo "skip_ready:       $SKIP_TRAIN_IF_READY"
    echo "backup_existing:  $BACKUP_EXISTING"
    echo "continue_error:   $CONTINUE_ON_ERROR"
    echo "viewer python:    $VIEWER_PYTHON"
    echo "convert radius:   $CONVERT_MAX_RADIUS"
    echo "convert scale:    $CONVERT_MAX_SCALE"
    echo "convert opacity:  $CONVERT_MIN_OPACITY"
    echo "batch log:        $BATCH_LOG"
    echo
    echo "scene별 command:"
  } | write_block "$output_target" "write"

  local idx=0
  for scene in "${SCENES[@]}"; do
    idx=$((idx + 1))
    image_dir="$(scene_image_dir "$scene")"
    port=$((PORT_START + idx - 1))
    model_dir="$(model_dir_for "$scene" "$image_dir")"
    input_ply="$(point_cloud_for "$model_dir")"
    output_ply="$(sibr_point_cloud_for "$model_dir")"
    local train_cmd=()
    local convert_cmd=()
    local post_cmd=()
    local viewer_cmd=()
    build_train_cmd "$scene" "$image_dir" "$port" train_cmd
    build_convert_cmd "$input_ply" "$output_ply" convert_cmd
    build_post_cmd "$scene" "$image_dir" "$port" post_cmd
    build_viewer_cmd "$model_dir" "$scene" viewer_cmd
    {
      printf '\n[%d/%d] %s / %s / port=%s\n' "$idx" "${#SCENES[@]}" "$scene" "$image_dir" "$port"
      echo "학습:"
      print_cmd "${train_cmd[@]}"
      if [[ "$RUN_CONVERT" == "1" ]]; then
        echo "SIBR 호환 변환:"
        printf '  PYTHONPATH=%q ' "${PROJECT_ROOT}/code"
        printf '%q ' "${convert_cmd[@]}"
        printf '\n'
      fi
      if [[ "$RUN_RENDER" == "1" ]]; then
        echo "render 후처리:"
        print_cmd "${post_cmd[@]}"
      fi
      echo "viewer 확인:"
      print_cmd "${viewer_cmd[@]}"
    } | write_block "$output_target" "append"
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
  input_ply="$(point_cloud_for "$model_dir")"
  output_ply="$(sibr_point_cloud_for "$model_dir")"
  train_cmd=()
  convert_cmd=()
  post_cmd=()
  viewer_cmd=()
  build_train_cmd "$scene" "$image_dir" "$port" train_cmd
  build_convert_cmd "$input_ply" "$output_ply" convert_cmd
  build_post_cmd "$scene" "$image_dir" "$port" post_cmd
  build_viewer_cmd "$model_dir" "$scene" viewer_cmd

  {
    echo
    echo "================================================================"
    printf '전체 진행: [%d/%d] %d%% | scene=%s | images=%s\n' "$idx" "${#SCENES[@]}" "$percent" "$scene" "$image_dir"
    date '+scene 시작: %Y-%m-%d %H:%M:%S %Z'
    echo "model: $model_dir"
    echo "학습 command:"
    print_cmd "${train_cmd[@]}"
    echo "----------------------------------------------------------------"
  } | tee -a "$BATCH_LOG"

  set +e
  "${train_cmd[@]}" 2>&1 | tee -a "$BATCH_LOG"
  train_status=${PIPESTATUS[0]}
  set -e

  convert_status=0
  post_status=0

  if [[ "$train_status" -eq 0 && "$RUN_CONVERT" == "1" ]]; then
    {
      echo
      echo "SIBR 호환 변환 command:"
      printf '  PYTHONPATH=%q ' "${PROJECT_ROOT}/code"
      printf '%q ' "${convert_cmd[@]}"
      printf '\n'
      echo "----------------------------------------------------------------"
    } | tee -a "$BATCH_LOG"
    if [[ ! -f "$input_ply" ]]; then
      echo "변환 입력 point_cloud가 없다: $input_ply" | tee -a "$BATCH_LOG"
      convert_status=4
    else
      set +e
      PYTHONPATH="${PROJECT_ROOT}/code${PYTHONPATH:+:$PYTHONPATH}" "${convert_cmd[@]}" 2>&1 | tee -a "$BATCH_LOG"
      convert_status=${PIPESTATUS[0]}
      set -e
    fi
  fi

  if [[ "$train_status" -eq 0 && "$convert_status" -eq 0 && "$RUN_RENDER" == "1" ]]; then
    {
      echo
      echo "render 후처리 command:"
      print_cmd "${post_cmd[@]}"
      echo "----------------------------------------------------------------"
    } | tee -a "$BATCH_LOG"
    set +e
    "${post_cmd[@]}" 2>&1 | tee -a "$BATCH_LOG"
    post_status=${PIPESTATUS[0]}
    set -e
  fi

  scene_end_epoch="$(date +%s)"
  scene_elapsed=$((scene_end_epoch - scene_start_epoch))
  batch_elapsed=$((scene_end_epoch - batch_start_epoch))
  scene_status=0

  if [[ "$train_status" -ne 0 ]]; then
    scene_status="$train_status"
  elif [[ "$convert_status" -ne 0 ]]; then
    scene_status="$convert_status"
  elif [[ "$post_status" -ne 0 ]]; then
    scene_status="$post_status"
  fi

  ply_status="missing"
  sibr_status="not_requested"
  if [[ -f "$input_ply" ]]; then
    ply_status="ok"
  fi
  if [[ "$RUN_CONVERT" == "1" ]]; then
    if [[ -f "$output_ply" ]]; then
      sibr_status="ok"
    else
      sibr_status="missing"
    fi
  fi

  if [[ "$scene_status" -eq 0 ]]; then
    SUMMARY+=("OK | ${scene} | ${image_dir} | ${scene_elapsed}s | point_cloud=${ply_status} | sibr=${sibr_status}")
  else
    SUMMARY+=("FAIL(${scene_status}) | ${scene} | ${image_dir} | ${scene_elapsed}s | train=${train_status} | convert=${convert_status} | post=${post_status}")
    overall_status="$scene_status"
  fi

  {
    echo "----------------------------------------------------------------"
    date '+scene 종료: %Y-%m-%d %H:%M:%S %Z'
    echo "scene exit status: $scene_status"
    echo "train status: $train_status"
    echo "convert status: $convert_status"
    echo "post status: $post_status"
    echo "scene 소요 시간: ${scene_elapsed}s"
    echo "batch 누적 시간: ${batch_elapsed}s"
    echo "point_cloud: $input_ply"
    if [[ "$RUN_CONVERT" == "1" ]]; then
      echo "sibr_safe: $output_ply"
    fi
    echo "viewer 확인 command:"
    print_cmd "${viewer_cmd[@]}"
    echo "현재까지 요약:"
    for item in "${SUMMARY[@]}"; do
      echo "  - $item"
    done
  } | tee -a "$BATCH_LOG"

  if [[ "$scene_status" -ne 0 && "$CONTINUE_ON_ERROR" != "1" ]]; then
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
  echo "전체 고퀄 batch 요약"
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
