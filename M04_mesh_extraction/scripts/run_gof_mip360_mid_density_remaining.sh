#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
flowers, garden, treehill에 대해 중간 density GOF/3DGS 학습을 순차 실행한다.

사용법:
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh --dry-run
  experiments/M04_mesh_extraction/scripts/run_gof_mip360_mid_density_remaining.sh --scenes "flowers treehill"

기본값:
  scenes:        flowers garden treehill
  iterations:    30000
  images:        images_4
  model suffix:  mid
  checkpoint:    1000 iteration마다 저장, 기존 checkpoint가 있으면 자동 재개
  density:       densify_until_iter=5000, densify_grad_threshold=0.001,
                 densification_interval=200, opacity_reset_interval=100000
  postprocess:   학습 완료 후 iteration_sibr_safe/point_cloud.ply 생성

옵션:
      --scenes LIST          실행할 scene 목록. flower는 flowers로 자동 보정한다.
  -n, --iterations N         각 scene의 학습 iteration 수. 기본값: 30000.
  -i, --images DIR           모든 scene에 사용할 이미지 폴더. 기본값: images_4.
      --suffix NAME          출력 model suffix. 기본값: mid.
      --gpu ID               CUDA_VISIBLE_DEVICES 값. 기본값: 0.
      --port-start PORT      scene별 port 시작값. 기본값: 6209.
      --data-device DEVICE   GOF data_device 인자. 기본값: cpu.
      --checkpoint-every N   N iteration마다 GOF checkpoint 저장. 기본값: 1000.
      --no-checkpoint        checkpoint 저장을 끈다.
      --no-resume            checkpoint 자동 재개를 끈다.
      --densify-until-iter N
                            GOF densify_until_iter. 기본값: 5000.
      --densify-grad-threshold VALUE
                            GOF densify_grad_threshold. 기본값: 0.001.
      --densification-interval N
                            GOF densification_interval. 기본값: 200.
      --opacity-reset-interval N
                            GOF opacity_reset_interval. 기본값: 100000.
      --percent-dense VALUE  GOF percent_dense override.
      --convert              SIBR 호환 PLY 변환을 실행한다. 기본값: 켬.
      --no-convert           SIBR 호환 PLY 변환을 건너뛴다.
      --max-radius VALUE     viewer-safe 변환의 최대 반경. 기본값: 12.
      --max-scale VALUE      viewer-safe 변환의 최대 Gaussian scale. 기본값: 1.0.
      --min-opacity VALUE    viewer-safe 변환의 최소 opacity. 기본값: 0.0.
      --viewer-python PATH   변환 모듈 실행에 사용할 Python. 기본값: .venv/bin/python.
      --skip-train-if-ready  이미 point_cloud가 있으면 학습을 건너뛰고 변환만 실행한다.
      --backup-existing      기존 model 디렉터리가 있으면 timestamp suffix를 붙여 백업한다.
      --continue-on-error    한 scene이 실패해도 다음 scene을 계속 실행한다.
      --dry-run              학습 없이 전체 실행 계획과 scene별 command만 출력한다.
  -h, --help                 이 도움말을 출력한다.

환경 변수 override:
  SCENES="flowers garden treehill"
  ITERATIONS=30000
  IMAGE_DIR=images_4
  MODEL_SUFFIX=mid
  GPU=0
  PORT_START=6209
EOF
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
SINGLE_SCRIPT="${SCRIPT_DIR}/run_gof_mip360_smoke.sh"
FILTER_MODULE="wind3dgs.m04_mesh_extraction.filter_viewer_safe_ply"
DEFAULT_VIEWER_PYTHON="${PROJECT_ROOT}/.venv/bin/python"

SCENES_RAW="${SCENES:-flowers garden treehill}"
ITERATIONS="${ITERATIONS:-30000}"
IMAGE_DIR="${IMAGE_DIR:-images_4}"
MODEL_SUFFIX="${MODEL_SUFFIX:-mid}"
GPU="${GPU:-0}"
PORT_START="${PORT_START:-6209}"
DATA_DEVICE="${DATA_DEVICE:-cpu}"
CHECKPOINT_EVERY="${CHECKPOINT_EVERY:-1000}"
RESUME_FROM_CHECKPOINT="${RESUME_FROM_CHECKPOINT:-1}"
DENSIFY_UNTIL_ITER="${DENSIFY_UNTIL_ITER:-5000}"
DENSIFY_GRAD_THRESHOLD="${DENSIFY_GRAD_THRESHOLD:-0.001}"
DENSIFICATION_INTERVAL="${DENSIFICATION_INTERVAL:-200}"
OPACITY_RESET_INTERVAL="${OPACITY_RESET_INTERVAL:-100000}"
PERCENT_DENSE="${PERCENT_DENSE:-}"
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
      shift 2
      ;;
    --suffix)
      MODEL_SUFFIX="$2"
      shift 2
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
    --checkpoint-every)
      CHECKPOINT_EVERY="$2"
      shift 2
      ;;
    --no-checkpoint)
      CHECKPOINT_EVERY=0
      shift
      ;;
    --no-resume)
      RESUME_FROM_CHECKPOINT=0
      shift
      ;;
    --densify-until-iter)
      DENSIFY_UNTIL_ITER="$2"
      shift 2
      ;;
    --densify-grad-threshold)
      DENSIFY_GRAD_THRESHOLD="$2"
      shift 2
      ;;
    --densification-interval)
      DENSIFICATION_INTERVAL="$2"
      shift 2
      ;;
    --opacity-reset-interval)
      OPACITY_RESET_INTERVAL="$2"
      shift 2
      ;;
    --percent-dense)
      PERCENT_DENSE="$2"
      shift 2
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

is_nonnegative_number() {
  [[ "$1" =~ ^([0-9]+([.][0-9]*)?|[.][0-9]+)([eE][+-]?[0-9]+)?$ ]]
}

for pair in \
  "iterations:$ITERATIONS" \
  "port-start:$PORT_START" \
  "checkpoint-every:$CHECKPOINT_EVERY" \
  "densify-until-iter:$DENSIFY_UNTIL_ITER" \
  "densification-interval:$DENSIFICATION_INTERVAL" \
  "opacity-reset-interval:$OPACITY_RESET_INTERVAL"
do
  key="${pair%%:*}"
  value="${pair#*:}"
  if [[ -n "$value" && ! "$value" =~ ^[0-9]+$ ]]; then
    echo "$key 값은 0 이상의 정수여야 한다: $value" >&2
    exit 2
  fi
done

for pair in \
  "densify-grad-threshold:$DENSIFY_GRAD_THRESHOLD" \
  "percent-dense:$PERCENT_DENSE" \
  "max-radius:$CONVERT_MAX_RADIUS" \
  "max-scale:$CONVERT_MAX_SCALE" \
  "min-opacity:$CONVERT_MIN_OPACITY"
do
  key="${pair%%:*}"
  value="${pair#*:}"
  if [[ -n "$value" ]] && ! is_nonnegative_number "$value"; then
    echo "$key 값은 0 이상의 숫자여야 한다: $value" >&2
    exit 2
  fi
done

if [[ "$MODEL_SUFFIX" =~ [[:space:]/] ]]; then
  echo "suffix에는 공백이나 /를 넣을 수 없다: $MODEL_SUFFIX" >&2
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

normalize_scene() {
  local scene="$1"
  if [[ "$scene" == "flower" ]]; then
    echo "flowers"
  else
    echo "$scene"
  fi
}

check_scene_name() {
  local scene="$1"
  case "$scene" in
    flowers|garden|treehill)
      ;;
    *)
      echo "이 임시 스크립트는 flowers, garden, treehill만 지원한다: $scene" >&2
      exit 2
      ;;
  esac
}

model_dir_for() {
  local scene="$1"
  local suffix_part=""
  if [[ -n "$MODEL_SUFFIX" ]]; then
    suffix_part="_${MODEL_SUFFIX}"
  fi
  echo "${PROJECT_ROOT}/experiments/M04_mesh_extraction/models/gof_mip360_${scene}_i${ITERATIONS}_${IMAGE_DIR}${suffix_part}"
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

read -r -a RAW_SCENES <<< "$SCENES_RAW"
SCENES=()
for raw_scene in "${RAW_SCENES[@]}"; do
  scene="$(normalize_scene "$raw_scene")"
  check_scene_name "$scene"
  SCENES+=("$scene")
done

if [[ "${#SCENES[@]}" -eq 0 ]]; then
  echo "실행할 scene이 없다." >&2
  exit 2
fi

for scene in "${SCENES[@]}"; do
  source_dir="${PROJECT_ROOT}/experiments/M04_mesh_extraction/raw/mipnerf360/${scene}"
  if [[ ! -d "$source_dir" ]]; then
    echo "scene 디렉터리가 없다: $source_dir" >&2
    exit 1
  fi
  if [[ ! -d "${source_dir}/${IMAGE_DIR}" ]]; then
    echo "이미지 디렉터리가 없다: ${source_dir}/${IMAGE_DIR}" >&2
    exit 1
  fi
  if [[ ! -f "${source_dir}/sparse/0/cameras.bin" || ! -f "${source_dir}/sparse/0/images.bin" || ! -f "${source_dir}/sparse/0/points3D.bin" ]]; then
    echo "COLMAP sparse 파일이 부족하다: ${source_dir}/sparse/0" >&2
    exit 1
  fi
done

LOG_DIR="${PROJECT_ROOT}/experiments/M04_mesh_extraction/outputs/logs"
BATCH_STAMP="$(date +%Y%m%d_%H%M%S)"
BATCH_LOG="${LOG_DIR}/gof_mip360_mid_density_i${ITERATIONS}_${IMAGE_DIR}_${BATCH_STAMP}.log"

build_train_cmd() {
  local scene="$1"
  local port="$2"
  local model_dir="$3"
  local -n out_cmd="$4"

  out_cmd=(
    "$SINGLE_SCRIPT"
    --scene "$scene"
    --iterations "$ITERATIONS"
    --images "$IMAGE_DIR"
    --model-dir "$model_dir"
    --gpu "$GPU"
    --port "$port"
    --data-device "$DATA_DEVICE"
    --checkpoint-every "$CHECKPOINT_EVERY"
    --densify-until-iter "$DENSIFY_UNTIL_ITER"
    --densify-grad-threshold "$DENSIFY_GRAD_THRESHOLD"
    --densification-interval "$DENSIFICATION_INTERVAL"
    --opacity-reset-interval "$OPACITY_RESET_INTERVAL"
  )
  if [[ "$RESUME_FROM_CHECKPOINT" == "1" ]]; then
    out_cmd+=(--resume)
  else
    out_cmd+=(--no-resume)
  fi
  if [[ -n "$PERCENT_DENSE" ]]; then
    out_cmd+=(--percent-dense "$PERCENT_DENSE")
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
  local scene="$1"
  local model_dir="$2"
  local -n out_cmd="$3"

  out_cmd=(
    env SIBR_DEFAULT_ITERATION=sibr_safe
    "${PROJECT_ROOT}/code/scripts/run_sibr_gaussian_viewer.sh"
    "$model_dir"
    "${PROJECT_ROOT}/experiments/M04_mesh_extraction/raw/mipnerf360/${scene}"
  )
}

print_plan() {
  local target="$1"
  {
    echo "== GOF Mip-NeRF 360 중간 density 임시 batch 계획 =="
    date '+생성: %Y-%m-%d %H:%M:%S %Z'
    echo "project:          $PROJECT_ROOT"
    echo "scenes:           ${SCENES[*]}"
    echo "iterations:       $ITERATIONS"
    echo "images:           $IMAGE_DIR"
    echo "model_suffix:     $MODEL_SUFFIX"
    echo "gpu:              $GPU"
    echo "port 시작값:      $PORT_START"
    echo "data_device:      $DATA_DEVICE"
    echo "checkpoint_every: $CHECKPOINT_EVERY"
    echo "resume:           $RESUME_FROM_CHECKPOINT"
    echo "densify_until_iter: $DENSIFY_UNTIL_ITER"
    echo "densify_grad_threshold: $DENSIFY_GRAD_THRESHOLD"
    echo "densification_interval: $DENSIFICATION_INTERVAL"
    echo "opacity_reset_interval: $OPACITY_RESET_INTERVAL"
    echo "percent_dense:    ${PERCENT_DENSE:-(default)}"
    echo "run_convert:      $RUN_CONVERT"
    echo "batch log:        $BATCH_LOG"
    echo
    echo "scene별 command:"
  } | write_block "$target" "write"

  local idx=0
  for scene in "${SCENES[@]}"; do
    idx=$((idx + 1))
    port=$((PORT_START + idx - 1))
    model_dir="$(model_dir_for "$scene")"
    input_ply="${model_dir}/point_cloud/iteration_${ITERATIONS}/point_cloud.ply"
    output_ply="${model_dir}/point_cloud/iteration_sibr_safe/point_cloud.ply"
    train_cmd=()
    convert_cmd=()
    viewer_cmd=()
    build_train_cmd "$scene" "$port" "$model_dir" train_cmd
    build_convert_cmd "$input_ply" "$output_ply" convert_cmd
    build_viewer_cmd "$scene" "$model_dir" viewer_cmd
    {
      printf '\n[%d/%d] %s / %s / port=%s\n' "$idx" "${#SCENES[@]}" "$scene" "$IMAGE_DIR" "$port"
      echo "model: $model_dir"
      echo "학습:"
      print_cmd "${train_cmd[@]}"
      if [[ "$RUN_CONVERT" == "1" ]]; then
        echo "SIBR 호환 변환:"
        printf '  PYTHONPATH=%q ' "${PROJECT_ROOT}/code"
        printf '%q ' "${convert_cmd[@]}"
        printf '\n'
      fi
      echo "viewer 확인:"
      print_cmd "${viewer_cmd[@]}"
    } | write_block "$target" "append"
  done
}

if [[ "$DRY_RUN" == "1" ]]; then
  print_plan /dev/stdout
  echo
  echo "dry_run: OK"
  exit 0
fi

mkdir -p "$LOG_DIR"
print_plan "$BATCH_LOG"

batch_start_epoch="$(date +%s)"
overall_status=0
SUMMARY=()

idx=0
for scene in "${SCENES[@]}"; do
  idx=$((idx + 1))
  port=$((PORT_START + idx - 1))
  model_dir="$(model_dir_for "$scene")"
  input_ply="${model_dir}/point_cloud/iteration_${ITERATIONS}/point_cloud.ply"
  output_ply="${model_dir}/point_cloud/iteration_sibr_safe/point_cloud.ply"
  train_cmd=()
  convert_cmd=()
  viewer_cmd=()
  build_train_cmd "$scene" "$port" "$model_dir" train_cmd
  build_convert_cmd "$input_ply" "$output_ply" convert_cmd
  build_viewer_cmd "$scene" "$model_dir" viewer_cmd
  scene_start_epoch="$(date +%s)"

  {
    echo
    echo "================================================================"
    printf '전체 진행: [%d/%d] scene=%s images=%s\n' "$idx" "${#SCENES[@]}" "$scene" "$IMAGE_DIR"
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

  scene_end_epoch="$(date +%s)"
  scene_elapsed=$((scene_end_epoch - scene_start_epoch))
  scene_status=0
  if [[ "$train_status" -ne 0 ]]; then
    scene_status="$train_status"
  elif [[ "$convert_status" -ne 0 ]]; then
    scene_status="$convert_status"
  fi

  if [[ "$scene_status" -eq 0 ]]; then
    SUMMARY+=("OK | ${scene} | ${scene_elapsed}s | model=${model_dir}")
  else
    SUMMARY+=("FAIL(${scene_status}) | ${scene} | train=${train_status} | convert=${convert_status}")
    overall_status="$scene_status"
  fi

  {
    echo "----------------------------------------------------------------"
    date '+scene 종료: %Y-%m-%d %H:%M:%S %Z'
    echo "scene exit status: $scene_status"
    echo "train status: $train_status"
    echo "convert status: $convert_status"
    echo "scene 소요 시간: ${scene_elapsed}s"
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
  echo "전체 중간 density batch 요약"
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
