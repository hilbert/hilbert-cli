#! /usr/bin/env bash

SELFDIR=`dirname "$0"`
SELFDIR=`cd "$SELFDIR" && pwd`
cd "${SELFDIR}/"

### set -e
## unset DISPLAY

#! NOTE: cleanup all previously started containers:
# docker ps -aq | xargs --no-run-if-empty docker rm -fv
# docker images -q -a | xargs --no-run-if-empty docker rmi

if [ -r "./station.cfg" ]; then
    . "./station.cfg"
fi

#if [ -r "./startup.cfg" ]; then
#    . "./startup.cfg"
#fi


station_default_app="${station_default_app:-$default_app}"

## TODO: FIXME: check stopped containers!
if [ -r "/tmp/lastapp.cfg" ]; then
    . "/tmp/lastapp.cfg"
else
    export current_app="${station_default_app}"
fi

#if hash ethtool 2>/dev/null; then
#   ## TODO: FIXME: 'NET_IF'???
#   for i in `LANG=C netstat -rn | awk '/^0.0.0.0/ {thif=substr($0,74); print thif;} /^default.*UG/ {thif=substr($0,65); print thif;}'`; 
#   do
##      echo "DEBUG: trying to enable WOL for interface: [$i]..."
##      sudo -n -P ethtool -s "$i" wol g
#      echo "DEBUG: checking WOL setting for interface: [$i]: "
#      sudo -n -P ethtool "$i" | grep Wake-on
#   done
#fi


if [ -r "./docker.cfg" ]; then
    . "./docker.cfg"
fi

if [ -n "${COMPOSE_FILE}" ]; then
  F="plain.${COMPOSE_FILE}"
  rm -f "$F"
  "./luncher.sh" config > "$F"
  export COMPOSE_FILE="$F"
fi

for d in ${background_services}; do
  echo "Starting Background Service: '${d}'..."
  "./luncher.sh" up -d "${d}"
done

unset COMPOSE_FILE

echo "Front GUI Application: '${current_app}'..."

if [ -n "${current_app}" ]; then
  echo "export current_app='${current_app}'" > "/tmp/lastapp.cfg.new~"
  "./luncher.sh" up -d "${current_app}"
  mv "/tmp/lastapp.cfg.new~" "/tmp/lastapp.cfg"
fi
