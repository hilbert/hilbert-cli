#!/usr/bin/env bash

if [ -z "$DOCKAPP_PATH" ]; then
>&2 echo "The DOCKAPP_PATH environment variable is not set. Set it to the directory where DockApp is installed".
exit 1
fi

if [ -z "$1" ]; then
  >&2 echo "First argument missing: station_id."
  exit 1
fi

station_id=$1

echo "Stopping station $station_id"
echo "1. Call finishall.sh"
cd $DOCKAPP_PATH
./finishall.sh $station_id
last_rc=$?

if [ "$last_rc" -ne "0" ]; then
  echo >&2 "finishall.sh returned $last_rc. Stopping station $station_id cancelled."
  exit 1;
fi

echo "2. Call shutdown.sh"
cd $DOCKAPP_PATH
./shutdown.sh $station_id -h now
last_rc=$?

if [ "$last_rc" -ne "0" ]; then
  echo >&2 "shutdown.sh returned $last_rc. Stopping station $station_id cancelled."
  exit 1;
fi

echo "Finished stopping station $station_id"