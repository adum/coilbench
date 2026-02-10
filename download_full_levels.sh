#!/usr/bin/env bash
set -euo pipefail

DATA_URL="https://github.com/adum/coilbench/releases/download/data-v1.0/boards.zip"
PUBLIC_DIR="levels_public"
SECRET_ARCHIVE="levels_secret_even.tar.enc"

echo "Fetching full level pack from ${DATA_URL}"

tmp_dir="$(mktemp -d)"
archive_path="${tmp_dir}/coilbench-levels.zip"
extract_dir="${tmp_dir}/extracted"
odd_tmp_dir="${tmp_dir}/odd_levels"
even_tmp_dir="${tmp_dir}/even_levels"
even_tar_path="${tmp_dir}/even_levels.tar"
encrypted_path="${tmp_dir}/${SECRET_ARCHIVE}"
trap 'rm -rf "${tmp_dir}"' EXIT

mkdir -p "${extract_dir}"
mkdir -p "${odd_tmp_dir}"
mkdir -p "${even_tmp_dir}"

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl is required but was not found in PATH." >&2
  exit 1
fi

curl -L "${DATA_URL}" -o "${archive_path}"

echo "Extracting archive..."
unzip -q "${archive_path}" -d "${extract_dir}"
src_levels_dir="$(find "${extract_dir}" -type d \( -name levels -o -name boards \) | head -n 1)"

if [[ -z "${src_levels_dir}" ]]; then
  echo "Unable to locate levels directory inside the archive" >&2
  exit 1
fi

for level_path in "${src_levels_dir}"/*; do
  level_name="$(basename "${level_path}")"
  if [[ ! "${level_name}" =~ ^[0-9]+$ ]]; then
    continue
  fi

  if (( 10#${level_name} % 2 == 1 )); then
    cp -a "${level_path}" "${odd_tmp_dir}/${level_name}"
  else
    cp -a "${level_path}" "${even_tmp_dir}/${level_name}"
  fi
done

if [[ -z "$(ls -A "${odd_tmp_dir}")" ]]; then
  echo "No odd levels found while splitting source pack." >&2
  exit 1
fi

if [[ -z "$(ls -A "${even_tmp_dir}")" ]]; then
  echo "No even levels found while splitting source pack." >&2
  exit 1
fi

while true; do
  read -r -s -p "Enter password to encrypt even levels: " encrypt_password
  echo
  read -r -s -p "Confirm password: " encrypt_password_confirm
  echo

  if [[ -z "${encrypt_password}" ]]; then
    echo "Password cannot be empty. Try again."
    continue
  fi
  if [[ "${encrypt_password}" != "${encrypt_password_confirm}" ]]; then
    echo "Passwords did not match. Try again."
    continue
  fi
  break
done

tar -C "${even_tmp_dir}" -cf "${even_tar_path}" .
printf '%s\n' "${encrypt_password}" | \
  openssl enc -aes-256-cbc -pbkdf2 -salt -pass stdin -in "${even_tar_path}" -out "${encrypted_path}"
unset encrypt_password
unset encrypt_password_confirm

if [[ ! -s "${encrypted_path}" ]]; then
  echo "Failed to create encrypted archive ${SECRET_ARCHIVE}" >&2
  exit 1
fi

echo "Replacing contents of ${PUBLIC_DIR} with odd levels"
rm -rf "${PUBLIC_DIR}"
mkdir -p "${PUBLIC_DIR}"
cp -a "${odd_tmp_dir}/." "${PUBLIC_DIR}/"

cp -a "${encrypted_path}" "${SECRET_ARCHIVE}"

echo "Installed odd levels into ${PUBLIC_DIR}"
echo "Wrote encrypted even-level archive to ${SECRET_ARCHIVE}"
