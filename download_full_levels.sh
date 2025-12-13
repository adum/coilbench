#!/usr/bin/env bash
set -euo pipefail

DATA_URL="https://github.com/adum/coilbench/releases/download/data-v1.0/boards.zip"
DEST_DIR="levels"

echo "Fetching full level pack from ${DATA_URL}"

tmp_dir="$(mktemp -d)"
archive_path="${tmp_dir}/coilbench-levels.zip"
extract_dir="${tmp_dir}/extracted"
trap 'rm -rf "${tmp_dir}"' EXIT

mkdir -p "${DEST_DIR}"
mkdir -p "${extract_dir}"

curl -L "${DATA_URL}" -o "${archive_path}"

echo "Extracting archive..."
unzip -q "${archive_path}" -d "${extract_dir}"

src_levels_dir="$(find "${extract_dir}" -type d \( -name levels -o -name boards \) | head -n 1)"

if [[ -z "${src_levels_dir}" ]]; then
  echo "Unable to locate levels directory inside the archive" >&2
  exit 1
fi

echo "Replacing contents of ${DEST_DIR}"
rm -rf "${DEST_DIR:?}/"*
cp -a "${src_levels_dir}/." "${DEST_DIR}/"

echo "All levels installed into ${DEST_DIR}"
