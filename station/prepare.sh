#! /bin/bash

### Preparation for actual docker-framework

SELFDIR=`dirname "$0"`
SELFDIR=`cd "$SELFDIR" && pwd`
cd "${SELFDIR}/"

#### TODO: needs some safety check to avoid multiple runs...

#! Finish our services (possible left-overs due to some crash)
#### ./finishall.sh # NOTE: no clean-up for left-overs for now

#! Clean-up the rest of containers
#?# docker ps -aq | xargs --no-run-if-empty docker rm -fv

#! All images??
# docker images -q -a | xargs --no-run-if-empty docker rmi

### add me to all the necessary groups etc ...
#if [ ! -L "$CFG_DIR/CFG" ]; then
#   ln -sf "$CFG_DIR" "$CFG_DIR/CFG"
#fi

#! TODO: FIXME: SUDO!
### ./ptmx.sh >/dev/null 2>&1 &

if [ -f ./OGL.tgz ];
then
  cp -fp ./OGL.tgz /tmp/ || sudo -n -P cp -fp ./OGL.tgz /tmp/
else
  echo "WARNING: Missing 'OGL.tgz'! Please regenerate!"
fi


# if [ -e "/tmp/lastapp.cfg" ]; then
#     
# if [ -w "/tmp/lastapp.cfg" ]; then
#     rm -f "/tmp/lastapp.cfg"
# else
#     sudo rm -f "/tmp/lastapp.cfg"
# fi
# 
# fi

if [ -r "./station.cfg" ]; then
    . "./station.cfg"
fi

#if [ -r "./startup.cfg" ]; then
#    . "./startup.cfg"
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

station_default_app="${station_default_app:-$default_app}"

if [ -r "/tmp/lastapp.cfg" ]; then
    . "/tmp/lastapp.cfg"
else
    export current_app="${station_default_app}"
fi

#! Pull for BG services
for d in ${background_services}; do
  echo "Pulling Image for background Service: '${d}'..."
  "./luncher.sh" pull --ignore-pull-failures "${d}"
done


#! Pull the default GUI app
if [ -n "${current_app}" ]; then
  echo "Pulling image for Front GUI Application: '${current_app}'..."
  "./luncher.sh" pull --ignore-pull-failures "${current_app}"
fi

#! Pull other possible GUI apps
for d in ${possible_apps}; do
  if [ ! "x$d" = "x${current_app}" ]; then
    echo "Pulling Image for background Service: '${d}'..."
    "./luncher.sh" pull --ignore-pull-failures "${d}"
  fi  
done

## TODO: FIXME: Cleanup using docker-gc!?!?

exit 0

