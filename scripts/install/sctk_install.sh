#!/usr/bin/env bash

#
# Script to install SCTK, the NIST Scoring Toolkit on Linux and macOS systems.
# More info at https://github.com/usnistgov/SCTK
#

SCTK_GITHUB_URL="https://github.com/usnistgov/SCTK/archive/refs/heads/master.zip"
SCTK_ZIP_NAME="./SCTK-master"
SCTK_DEST_DIR="../../resources/sctk"

curl -LJO "${SCTK_GITHUB_URL}"

unzip "${SCTK_ZIP_NAME}.zip"
rm "${SCTK_ZIP_NAME}.zip"

mkdir -p "${SCTK_DEST_DIR}"
cp -r "${SCTK_ZIP_NAME:?}/"* "${SCTK_DEST_DIR}" && rm -Rf "${SCTK_ZIP_NAME}"

cd "${SCTK_DEST_DIR}" || exit

make config
make all
make check
make install
make doc