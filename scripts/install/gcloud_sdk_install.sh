#!/usr/bin/env bash

#
# Script to install and configure Google Cloud SDK on Linux or macOS systems.
# More info at https://cloud.google.com/sdk/docs/install
#

# Check and update with latest version number in https://cloud.google.com/sdk/docs/install
GCLOUD_SDK_VERSION="338.0.0"
GCLOUD_SDK_PACKAGE_NAME="google-cloud-sdk-${GCLOUD_SDK_VERSION}-"
GCLOUD_SDK_URL="https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/"

# Detect OS kernel
OS_KERNEL="$(uname -s)"
case "${OS_KERNEL}" in
    Linux*)     kernel="linux";;
    Darwin*)    kernel="darwin";;
    *)          kernel="unsupported"
esac

if [[ "${kernel}" == "unsupported" ]]; then
  echo "Kernel ${OS_KERNEL} not supported."
  exit 1
else
  echo "${OS_KERNEL} kernel detected."
  GCLOUD_SDK_PACKAGE_NAME+="${kernel}-"
fi

# Detect OS architecture
OS_ARCHITECTURE="$(getconf LONG_BIT)"
if [[ "${OS_ARCHITECTURE}" == "64" ]]; then
  GCLOUD_SDK_PACKAGE_NAME+="x86_64.tar.gz"
else
  GCLOUD_SDK_PACKAGE_NAME+="x86.tar.gz"
fi
echo "Detected ${OS_ARCHITECTURE} bit architecture."

# Download Google Cloud SDK package
curl -O "${GCLOUD_SDK_URL}${GCLOUD_SDK_PACKAGE_NAME}"

# Extract archive
tar xfz "${GCLOUD_SDK_PACKAGE_NAME}"

cd ./google-cloud-sdk || exit

# Install gcloud SDK
./install.sh

# Initialize gcloud SDK
./bin/gcloud init

# Set up application default authorization for gcloud
./bin/gcloud auth application-default login

# Clean up
rm ../"${GCLOUD_SDK_PACKAGE_NAME}"
rm -Rf ../google-cloud-sdk