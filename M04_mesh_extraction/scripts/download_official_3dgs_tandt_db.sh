#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DOWNLOAD_DIR="${ROOT_DIR}/downloads"
RAW_DIR="${ROOT_DIR}/raw"
URL="https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/datasets/input/tandt_db.zip"
ARCHIVE="${DOWNLOAD_DIR}/tandt_db.zip"
EXPECTED_BYTES="682628995"

mkdir -p "${DOWNLOAD_DIR}" "${RAW_DIR}"

echo "Downloading official 3DGS T&T+DB COLMAP dataset..."
echo "URL: ${URL}"
echo "Destination: ${ARCHIVE}"
curl -L --continue-at - --output "${ARCHIVE}" "${URL}"

ACTUAL_BYTES="$(wc -c < "${ARCHIVE}")"
echo "Downloaded bytes: ${ACTUAL_BYTES}"
if [[ "${ACTUAL_BYTES}" != "${EXPECTED_BYTES}" ]]; then
  echo "Warning: expected ${EXPECTED_BYTES} bytes from HEAD check."
fi

echo "Extracting to ${RAW_DIR}..."
unzip -q -n "${ARCHIVE}" -d "${RAW_DIR}"

echo "Candidate COLMAP scene folders:"
find "${RAW_DIR}" -maxdepth 4 -type d -name sparse -print | sort
