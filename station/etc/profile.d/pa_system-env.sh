# check for system wide PA setup
if [ -z "${PULSE_SERVER}" ]; then
  _PA_SYSTEM_PATH="/var/run/pulse"
  if [ -S "${_PA_SYSTEM_PATH}/native" ]; then
    export PULSE_SERVER="${_PA_SYSTEM_PATH}/native"
    if [ -f "${_PA_SYSTEM_PATH}/.config/pulse/cookie" ]; then
#      # TODO: FIXME: move the following to PA initialization unit!?
#      sudo chown -R pulse:pulse "${_PA_SYSTEM_PATH}/.config"
#      sudo chmod -R a+r "${_PA_SYSTEM_PATH}/.config"
      export PULSE_COOKIE="${_PA_SYSTEM_PATH}/.config/pulse/cookie"
    fi
  fi
  unset _PA_SYSTEM_PATH
fi

# check for user's (active!) PA session
if [ -z "${PULSE_SERVER}" ]; then
  if [ -S "/run/user/${UID}/pulse/native" ]; then
    export PULSE_SERVER="/run/user/${UID}/pulse/native"
    export PULSE_COOKIE="${HOME}/.config/pulse/cookie"
  fi
fi
