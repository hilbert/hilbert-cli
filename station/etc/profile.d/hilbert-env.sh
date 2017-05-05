if [ -z "${DOCKER_COMPOSE}" ]; then

  _PREFIXES="${HOME}/bin /opt/hilbert-cli/bin"

  for _D in ${_PREFIXES} ; do
    DOCKER_COMPOSE="${_D}/docker-compose"
    if test -x "${DOCKER_COMPOSE}" ; then 
      export DOCKER_COMPOSE
      break
    fi
  done

  unset _PREFIXES
  unset _D
fi

if [ -z "${HILBERT_STATION}" ]; then

  _PREFIXES="${HOME}/bin /opt/hilbert-cli/bin"

  for _D in ${_PREFIXES} ; do
    HILBERT_STATION="${_D}/hilbert-station"
    if test -x "${HILBERT_STATION}" ; then 
      export HILBERT_STATION
      if ! echo ${PATH} | /bin/grep -q ${_D} ; then
        export PATH=${_D}:${PATH}
      fi
      break
    fi
  done

  unset _PREFIXES
  unset _D
fi

