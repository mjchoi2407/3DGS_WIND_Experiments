#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
cd "$PROJECT_ROOT"

URL="https://dl.fbaipublicfiles.com/co3d/umbrella.zip"
ZIPDIR="experiments/M04_mesh_extraction/downloads/co3d/category_zips"
OUTPUT="${ZIPDIR}/umbrella.zip"
EXPECTED_BYTES=41944422600
LOG="${ZIPDIR}/umbrella_wget_resume_latest.log"
LOCKDIR="${OUTPUT}.wget-resume.lock"

if ! mkdir "$LOCKDIR" 2>/dev/null; then
  echo "Another umbrella wget-resume run may be active: $LOCKDIR"
  echo "If you are sure it is stale, remove it with:"
  echo "  rmdir '$LOCKDIR'"
  exit 1
fi
trap 'rmdir "$LOCKDIR" 2>/dev/null || true' EXIT

mkdir -p "$ZIPDIR"

{
  echo "== CO3D umbrella.zip wget resume =="
  date '+started: %Y-%m-%d %H:%M:%S %Z'
  echo "project:  $PROJECT_ROOT"
  echo "url:      $URL"
  echo "output:   $OUTPUT"
  echo "expect:   $EXPECTED_BYTES bytes"
  echo "log:      $LOG"
  echo
  echo "Current output size:"
  if [[ -f "$OUTPUT" ]]; then
    stat -c '  %n %s bytes' "$OUTPUT"
  else
    echo "  missing"
  fi
  echo
  echo "Resuming with wget -c. Progress is printed below."
  echo
} | tee "$LOG"

set +e
wget -c --progress=dot:giga -P "$ZIPDIR" "$URL" 2>&1 | tee -a "$LOG"
status=${PIPESTATUS[0]}
set -e

{
  echo
  date '+finished: %Y-%m-%d %H:%M:%S %Z'
  echo "exit_status: $status"
  echo "Final output size:"
  if [[ -f "$OUTPUT" ]]; then
    stat -c '  %n %s bytes' "$OUTPUT"
    actual="$(stat -c '%s' "$OUTPUT")"
    if [[ "$actual" == "$EXPECTED_BYTES" ]]; then
      echo "size_check: OK"
      echo "Next check:"
      echo "  unzip -tq '$OUTPUT'"
    else
      echo "size_check: NOT COMPLETE ($actual != $EXPECTED_BYTES)"
    fi
  else
    echo "  missing"
  fi
} | tee -a "$LOG"

exit "$status"
