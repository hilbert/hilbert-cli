#!/bin/bash -xv

SELFDIR=`dirname "$0"`
SELFDIR=`cd "$SELFDIR" && pwd`
cd "$SELFDIR/"
## set -e

TARGET_HOST_NAME="$1"
shift
ARGS=$@

./topswitch.sh "${TARGET_HOST_NAME}" ${ARGS} && \
./lastapp.sh "${TARGET_HOST_NAME}"

exit $?
