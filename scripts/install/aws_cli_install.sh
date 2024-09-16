#!/usr/bin/env bash

#
# Script to install and configure AWS CLI on Linux and macOS systems (only 64-bit architecture support).
# More info at https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-welcome.html
#

AWS_CLI_URL="https://awscli.amazonaws.com/"
AWS_CLI_PACKAGE_NAME_LINUX="awscli-exe-linux-x86_64.zip"
AWS_CLI_PACKAGE_NAME_MACOS="AWSCLIV2.pkg"

function mac_os_setup {
  # Install AWS CLI package
  sudo installer -pkg ${AWS_CLI_PACKAGE_NAME_MACOS} -target /

    # Clean up
  rm ./"${AWS_CLI_PACKAGE_NAME_MACOS}"
}

function linux_setup {
  # Extract archive
  unzip "${AWS_CLI_PACKAGE_NAME_LINUX}"

  # Install AWS CLI
  sudo ./aws/install

  # Clean up
  rm ./"${AWS_CLI_PACKAGE_NAME_LINUX}"
  rm -Rf ./aws
}

# Detect OS kernel
OS_KERNEL="$(uname -s)"
case "${OS_KERNEL}" in
    Linux*)     AWS_CLI_PACKAGE_NAME="${AWS_CLI_PACKAGE_NAME_LINUX}";;
    Darwin*)    AWS_CLI_PACKAGE_NAME="${AWS_CLI_PACKAGE_NAME_MACOS}";;
    *)          AWS_CLI_PACKAGE_NAME="unsupported"
esac

if [[ "${AWS_CLI_PACKAGE_NAME}" == "unsupported" ]]; then
  echo "Kernel ${OS_KERNEL} not supported."
  exit 1
else
  echo "${OS_KERNEL} kernel detected."
fi

# Download AWS CLI package
curl -O "${AWS_CLI_URL}${AWS_CLI_PACKAGE_NAME}"

# Launch setup function based on detected kernel
if [[ "${AWS_CLI_PACKAGE_NAME}" == "${AWS_CLI_PACKAGE_NAME_LINUX}" ]]; then
  linux_setup
else
  mac_os_setup
fi

# Configure AWS CLI
aws configure
