#!/usr/bin/env bash

#
# Script to compile all .proto files in specified ${PROTO_BUFFERS_DIR}.
#

DESTINATION_DIR="../modules/compiled"
PROTO_BUFFERS_DIR="../protocol-buffers"

cd "${PROTO_BUFFERS_DIR}" || exit

for FILE in *; do
  protoc -I="${PROTO_BUFFERS_DIR}" --python_out="${DESTINATION_DIR}" "${PROTO_BUFFERS_DIR}/${FILE}";
done
