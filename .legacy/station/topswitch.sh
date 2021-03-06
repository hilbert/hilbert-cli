#! /usr/bin/env bash

SELFDIR=`dirname "$0"`
SELFDIR=`cd "$SELFDIR" && pwd`
cd "${SELFDIR}/"

if [ -r "./station.cfg" ]; then
    . "./station.cfg"
fi

if [ -r "/tmp/lastapp.cfg" ]; then
    . "/tmp/lastapp.cfg"
    old="${current_app}"
    unset current_app
    mv -f "/tmp/lastapp.cfg" "/tmp/lastapp.cfg.bak"
else
    old="${default_app}"
fi

if [ -n "${COMPOSE_FILE}" ]; then
  F="plain.${COMPOSE_FILE}"
  rm -f "$F"
  "./luncher.sh" config > "$F"
  export COMPOSE_FILE="$F"
fi

"./luncher.sh" stop -t 10 "${old}"
"./luncher.sh" kill -s SIGTERM  "${old}"
"./luncher.sh" kill -s SIGKILL  "${old}"
"./luncher.sh" rm -f "${old}"
unset old

#### ARGUMENT!!!
export current_app="$@"
echo "export current_app='${current_app}'" > "/tmp/lastapp.cfg.new~"
"./luncher.sh" up -d "$current_app" && mv -f "/tmp/lastapp.cfg.new~" "/tmp/lastapp.cfg"
