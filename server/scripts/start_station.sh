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

echo "Starting station $station_id"

echo "1. Call start.sh"
cd $DOCKAPP_PATH
./start.sh $station_id

if [ "$?" -ne "0" ]; then
  echo >&2 "start.sh returned $?. Starting station $station_id cancelled."
  exit $?;
fi

echo "2. Call deploy.sh"
cd $DOCKAPP_PATH
./deploy.sh $station_id

if [ "$?" -ne "0" ]; then
  echo >&2 "deploy.sh returned $?.  Starting station $station_id cancelled."
  exit $?;
fi

echo "3. Call prepare.sh"
cd $DOCKAPP_PATH
./prepare.sh $station_id

if [ "$?" -ne "0" ]; then
  echo >&2 "prepare.sh returned $?. Starting station $station_id cancelled."
  exit $?;
fi

echo "4. Call default_update.sh"
cd $DOCKAPP_PATH
./default_update.sh $station_id

if [ "$?" -ne "0" ]; then
  echo >&2 "default_update.sh returned $?. Starting station $station_id cancelled."
  exit $?;
fi

echo "Finished starting station $station_id"