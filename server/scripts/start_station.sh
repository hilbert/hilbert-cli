#!/usr/bin/env bash

if [ -z "$HILBERT_CLI_PATH" ]; then
  >&2 echo "The HILBERT_CLI_PATH environment variable is not set. Set it to the directory where hilbert-cli is installed".
  exit 1
fi

if [ -z "$1" ]; then
  >&2 echo "First argument missing: station_id."
  exit 1
fi

station_id=$1

echo "Starting station $station_id"

echo "1. Call start.sh"
cd $HILBERT_CLI_PATH
./start.sh $station_id
last_rc=$?

if [ "$last_rc" -ne "0" ]; then
  echo >&2 "start.sh returned $last_rc. Starting station $station_id cancelled."
  exit 1;
fi

echo "2. Call deploy.sh"
cd $HILBERT_CLI_PATH
./deploy.sh $station_id
last_rc=$?

if [ "$last_rc" -ne "0" ]; then
  echo >&2 "deploy.sh returned $last_rc.  Starting station $station_id cancelled."
  exit 1;
fi

echo "3. Call prepare.sh"
cd $HILBERT_CLI_PATH
./prepare.sh $station_id
last_rc=$?

if [ "$last_rc" -ne "0" ]; then
  echo >&2 "prepare.sh returned $last_rc. Starting station $station_id cancelled."
  exit 1;
fi

echo "4. Call default_update.sh"
cd $HILBERT_CLI_PATH
./default_update.sh $station_id
last_rc=$?

if [ "$last_rc" -ne "0" ]; then
  echo >&2 "default_update.sh returned $last_rc. Starting station $station_id cancelled."
  exit 1;
fi

echo "Finished starting station $station_id"