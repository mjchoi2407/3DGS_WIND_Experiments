#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "$PROJECT_ROOT"

OUTPUT="experiments/M04_mesh_extraction/downloads/co3d/category_zips/umbrella.zip"
PARTDIR="${OUTPUT}.parts"
EXPECTED_BYTES=41944422600
LOG="experiments/M04_mesh_extraction/downloads/co3d/category_zips/umbrella_assemble_latest.log"
LOCKDIR="${OUTPUT}.assemble.lock"
CHUNK_MIB="${CHUNK_MIB:-16}"

if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "Another assemble run may be active: $LOCKDIR"
  echo "If you are sure it is stale, remove it with:"
  echo "  rmdir '$LOCKDIR'"
  exit 1
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null || true' EXIT

mkdir -p "$(dirname "$LOG")"

{
  echo "== CO3D umbrella.zip visible assemble =="
  date '+started: %Y-%m-%d %H:%M:%S %Z'
  echo "project: $PROJECT_ROOT"
  echo "output:  $OUTPUT"
  echo "parts:   $PARTDIR"
  echo "expect:  $EXPECTED_BYTES bytes"
  echo "chunk:   ${CHUNK_MIB} MiB"
  echo "log:     $LOG"
  echo
  echo "Current output size:"
  stat -c '  %n %s bytes' "$OUTPUT"
  echo
  echo "Part files:"
  find "$PARTDIR" -maxdepth 1 -type f -name 'part_[0-9][0-9][0-9]' -printf '  %f %s bytes\n' | sort
  echo
  echo "Assembling. Progress should print every ${CHUNK_MIB} MiB."
  echo
} | tee "$LOG"

set +e
PYTHONUNBUFFERED=1 python3 \
  experiments/M04_mesh_extraction/scripts/assemble_parts_resume.py \
  "$OUTPUT" \
  "$PARTDIR" \
  "$EXPECTED_BYTES" \
  --chunk-mib "$CHUNK_MIB" \
  --verify-existing 2>&1 | tee -a "$LOG"
status=${PIPESTATUS[0]}
set -e

{
  echo
  date '+finished: %Y-%m-%d %H:%M:%S %Z'
  echo "exit_status: $status"
  echo "Final output size:"
  stat -c '  %n %s bytes' "$OUTPUT"
  if [[ "$(stat -c '%s' "$OUTPUT")" == "$EXPECTED_BYTES" ]]; then
    echo "size_check: OK"
    echo "Next optional check:"
    echo "  unzip -tq '$OUTPUT'"
  else
    echo "size_check: NOT COMPLETE"
  fi
} | tee -a "$LOG"

exit "$status"
