#!/usr/bin/env bash

declare -r LOG_BASEDIR="${HOME}/.config/hilbert-station/logs/"
mkdir -p "${LOG_BASEDIR}"

# reuse latest log-dir!
declare -r LOG_LATEST="${LOG_BASEDIR}/latest"

if [[ -w "${LOG_LATEST}" ]]; then
  declare -r LOG_DIR="${LOG_LATEST}"
else
  declare -r LOG_DIR="${LOG_BASEDIR}/$(date)_"
  mkdir -p "${LOG_DIR}"
fi

declare -r HILBERT_STATION="${HOME}/bin/hilbert-station"
declare -r HILBERT_LOG="${LOG_DIR}/autostop.log"

function Status() {
    local n="$1"

    echo "Status Query [$n]..." 1>>"${HILBERT_LOG}"

    ps auwwwx 1>>"${LOG_DIR}/$n.ps.log" 2>&1
    docker ps -a 1>>"${LOG_DIR}/$n.docker_ps.log" 2>&1

    "${HILBERT_STATION}" -vvV 1>>"${LOG_DIR}/$n.status.log" 2>&1
    "${HILBERT_STATION}" -vvv list_applications 1>>"${LOG_DIR}/$n.applications.log" 2>&1
    "${HILBERT_STATION}" -vvv list_services 1>>"${LOG_DIR}/$n.services.log" 2>&1
    return $?
}

function HilbertStop() {
    echo "[[[[[[[[[[[[[[[[[[[[[ Stopping Hilbert: ]]]]]]]]]]]]]]]]]]]]]]"
    "${HILBERT_STATION}" -vvvvt stop 2>&1
    return $?
}


(echo "LOG_LATEST: ${LOG_LATEST}"; ls -l "${LOG_LATEST}"; ls -l "$(readlink -f "${LOG_LATEST}")") 1>>"${HILBERT_LOG}" 2>&1
(echo "HILBERT_STATION: ${HILBERT_STATION}..."; ls -l "${HILBERT_STATION}"; ls -l "$(readlink -f "${HILBERT_STATION}")") 1>>"${HILBERT_LOG}" 2>&1

Status 2
HilbertStop 1>>"${HILBERT_LOG}" 2>&1
Status 3

exit 0
