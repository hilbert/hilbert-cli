#!/usr/bin/env bash

declare -r LOG_BASEDIR="${HOME}/.config/hilbert-station/logs/"
mkdir -p "${LOG_BASEDIR}"

declare -r LOG_DIR="${LOG_BASEDIR}/$(date)"
mkdir -p "${LOG_DIR}"

# latest log-dir - for later use!
declare -r LOG_LATEST="${LOG_BASEDIR}/latest"

declare -r HILBERT_STATION="${HOME}/bin/hilbert-station"
declare -r HILBERT_LOG="${LOG_DIR}/autostart.log"

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

function StartHttpd() {
    local HTTPD="${HOME}/bin/www.sh"
    ## NOTE: temporary start simple http server with WebGL Applications at localhost:8080!
    if [[ -x "${HTTPD}" ]]; then
        local HTTPD_PORT="8080"

        local WWW_LOG="${LOG_DIR}/www.log"
        local BASE_WWW_LOG="${LOG_BASEDIR}/www.log"

        # NOTE: port :8080!
        netstat -lnt | grep -E ":${HTTPD_PORT} " | grep -E 'LISTEN *$' 1>>/dev/null 2>&1
        if [[ $? -ne 0 ]]; then
            local ret

            ls -la "${HTTPD}" 1>>"${WWW_LOG}" 2>&1
            "${HTTPD}" 1>>"${WWW_LOG}" 2>&1 &
            ret=$?

            if [[ ${ret} -ne 0 ]]; then
                echo "WARNING: Starting HTTPD on ${HTTPD_PORT} returned with code: ${ret}" 1>>"${WWW_LOG}"
            else
                [[ -L "${BASE_WWW_LOG}" ]] && unlink "${BASE_WWW_LOG}"
                ln -sf "${WWW_LOG}" "${BASE_WWW_LOG}"
            fi
        else
            echo "WARNING: HTTPD_PORT:${HTTPD_PORT} seems to be busy... Is HTTPD server already running?" 1>>"${WWW_LOG}"
        fi
    fi
    return $?
}

function HilbertInit() {
    echo "[[[[[[[[[[[[[[[[[[[[[ Preparing/Initializing Hilbert: ]]]]]]]]"
    hilbert-station -vv init  2>&1
    return $?
}

function HilbertStart() {
    echo "[[[[[[[[[[[[[[[[[[[[[ Starting Hilbert: ]]]]]]]]]]]]]]]]]]]]]]"
    hilbert-station -vvvvt start  2>&1
    return $?
}


(echo "HILBERT_STATION: ${HILBERT_STATION}..."; ls -l "${HILBERT_STATION}"; ls -l "$(readlink -f "${HILBERT_STATION}")") 1>>"${HILBERT_LOG}" 2>&1

Status 0

StartHttpd

HilbertInit 1>>"${LOG_DIR}/init.log" 2>&1

HilbertStart 1>>"${LOG_DIR}/start.log" 2>&1

Status 1

# NOTE: update the latest logging output directory
[[ -L "${LOG_LATEST}" ]] && unlink "${LOG_LATEST}"
ln -sf "${LOG_DIR}" "${LOG_LATEST}"

(echo "LOG_LATEST: ${LOG_LATEST}"; ls -l "${LOG_LATEST}"; ls -l "$(readlink -f "${LOG_LATEST}")") 1>>"${HILBERT_LOG}" 2>&1

exit 0
