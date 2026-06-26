#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 3 || $# -gt 4 ]]; then
  echo "Usage: $0 URL OUTPUT_PATH EXPECTED_BYTES [JOBS]" >&2
  exit 2
fi

url="$1"
output="$2"
expected_bytes="$3"
jobs="${4:-8}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

partdir="${output}.parts"
mkdir -p "$partdir"

part0="${partdir}/part_000"
ranges_file="${partdir}/ranges.tsv"
reuse_existing_ranges=0
if [[ -f "$part0" ]]; then
  base_bytes="$(stat -c '%s' "$part0")"
  if [[ -f "$output" ]]; then
    output_bytes="$(stat -c '%s' "$output")"
    if [[ "$output_bytes" -eq "$expected_bytes" ]]; then
      echo "Already complete: $output"
      exit 0
    fi
    echo "Refusing to continue: both $output and $part0 exist." >&2
    exit 1
  fi
elif [[ -f "$ranges_file" && -f "$output" ]]; then
  output_bytes="$(stat -c '%s' "$output")"
  if [[ "$output_bytes" -eq "$expected_bytes" ]]; then
    echo "Already complete: $output"
    exit 0
  fi
  first_range_start="$(awk 'NR == 1 {print $2}' "$ranges_file")"
  if [[ -n "$first_range_start" && "$output_bytes" -ge "$first_range_start" ]]; then
    base_bytes="$first_range_start"
    reuse_existing_ranges=1
    echo "Detected in-progress assembly; reusing existing ranges from $ranges_file"
  else
    echo "Refusing to continue: existing output does not match saved ranges." >&2
    exit 1
  fi
elif [[ -f "$output" ]]; then
  output_bytes="$(stat -c '%s' "$output")"
  if [[ "$output_bytes" -eq "$expected_bytes" ]]; then
    echo "Already complete: $output"
    exit 0
  fi
  if [[ "$output_bytes" -gt "$expected_bytes" ]]; then
    echo "Output is larger than expected: $output_bytes > $expected_bytes" >&2
    exit 1
  fi
  mv "$output" "$part0"
  base_bytes="$output_bytes"
else
  : > "$part0"
  base_bytes=0
fi

if [[ "$base_bytes" -gt "$expected_bytes" ]]; then
  echo "Existing partial is larger than expected: $base_bytes > $expected_bytes" >&2
  exit 1
fi

if [[ "$reuse_existing_ranges" -eq 0 ]]; then
  rm -f "$ranges_file"

  remaining=$((expected_bytes - base_bytes))
  if [[ "$remaining" -gt 0 ]]; then
    chunk_bytes=$(((remaining + jobs - 1) / jobs))
    idx=1
    start="$base_bytes"
    while [[ "$start" -lt "$expected_bytes" ]]; do
      end=$((start + chunk_bytes - 1))
      if [[ "$end" -ge "$expected_bytes" ]]; then
        end=$((expected_bytes - 1))
      fi
      printf "%03d\t%d\t%d\n" "$idx" "$start" "$end" >> "$ranges_file"
      start=$((end + 1))
      idx=$((idx + 1))
    done
  fi
fi

download_chunk() {
  local idx="$1"
  local start="$2"
  local end="$3"
  local out="${partdir}/part_${idx}"
  local tmp="${out}.tmp"
  local wanted=$((end - start + 1))

  if [[ -f "$out" ]]; then
    local have
    have="$(stat -c '%s' "$out")"
    if [[ "$have" -eq "$wanted" ]]; then
      echo "skip part_${idx} (${have} bytes)"
      return 0
    fi
  fi

  rm -f "$tmp" "$out"
  echo "download part_${idx}: bytes ${start}-${end}"
  curl --silent --show-error -fL --retry 5 --retry-delay 5 --retry-all-errors \
    --range "${start}-${end}" \
    --output "$tmp" \
    "$url"

  local got
  got="$(stat -c '%s' "$tmp")"
  if [[ "$got" -ne "$wanted" ]]; then
    echo "part_${idx} has wrong size: $got != $wanted" >&2
    exit 1
  fi
  mv "$tmp" "$out"
  echo "done part_${idx}: ${got} bytes"
}

export url partdir
export -f download_chunk

if [[ -s "$ranges_file" ]]; then
  xargs -P "$jobs" -n 3 bash -c 'download_chunk "$@"' _ < "$ranges_file"
fi

PYTHONUNBUFFERED=1 python3 \
  "${script_dir}/assemble_parts_resume.py" \
  "$output" \
  "$partdir" \
  "$expected_bytes" \
  --chunk-mib "${ASSEMBLE_CHUNK_MIB:-64}" \
  --verify-existing
