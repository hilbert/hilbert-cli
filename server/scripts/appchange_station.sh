#!/usr/bin/env bash

if [ -z "$HILBERT_CLI_PATH" ]; then
>&2 echo "The HILBERT_CLI_PATH environment variable is not set. Set it to the directory where hilbert-cli is installed".
exit 1
fi

if [ -z "$1" ]; then
  >&2 echo "First argument missing: station_id."
  exit 1
fi

if [ -z "$2" ]; then
  >&2 echo "Second argument missing: app_id."
  exit 1
fi

station_id=$1
app_id=$2

echo "Changing top app of station $station_id to $app_id"

cd $HILBERT_CLI_PATH
./topswitch_update.sh $station_id $app_id
last_rc=$?

if [ "$last_rc" -ne "0" ]; then
  echo >&2 "topswitch_update.sh returned $last_rc. Changing top app of station $station_id cancelled."
  exit 1;
fi

echo "Finished changing top app of $station_id"