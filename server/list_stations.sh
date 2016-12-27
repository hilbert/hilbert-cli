#!/usr/bin/env bash

__SELFDIR=`dirname "$0"`
__SELFDIR=`cd "${__SELFDIR}" && pwd`

#if [ -z "${HILBERT_CLI_PATH}" ]; then
#    >&2 echo "The HILBERT_CLI_PATH environment variable is not set. Set it to the directory where 'hilbert' is installed!".
#    exit 1
#fi

export HILBERT_CLI_PATH="${HILBERT_CLI_PATH:-${__SELFDIR}}"

if [ -z "${HILBERT_SERVER_CONFIG_PATH}" ]; then
    >&2 echo "The HILBERT_SERVER_CONFIG_PATH environment variable is not set. Set it to the path of 'Hilbert.yml'!".
    exit 1
fi

# export HILBERT_SERVER_CONFIG_PATH="${HILBERT_SERVER_CONFIG_PATH:-${__SELFDIR}/Hilbert.yml}"

if [ ! -d "${HILBERT_CLI_PATH}" ]; then
    >&2 echo "'${HILBERT_CLI_PATH}' directory not found!"
    exit 1
fi

if [ ! -f "${HILBERT_CLI_PATH}/hilbert" ]; then
    >&2 echo "'hilbert' not found in '${HILBERT_CLI_PATH}'!"
    exit 1
fi

if [ ! -f "${HILBERT_SERVER_CONFIG_PATH}" ]; then
    >&2 echo "Hilbert Configuration file '${HILBERT_SERVER_CONFIG_PATH}' not found!"
    exit 1
fi

if [ ! -r "${HILBERT_SERVER_CONFIG_PATH}" ]; then
    >&2 echo "Hilbert Configuration file '${HILBERT_SERVER_CONFIG_PATH}' is unreadable!"
    exit 1
fi

exec "${HILBERT_CLI_PATH}/hilbert" -q list_stations --configfile "${HILBERT_SERVER_CONFIG_PATH}" --format dashboard
