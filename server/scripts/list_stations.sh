#!/usr/bin/env bash

if [ -z "$HILBERT_CLI_PATH" ]; then
>&2 echo "The HILBERT_CLI_PATH environment variable is not set. Set it to the directory where hilbert-cli is installed".
exit 1
fi

if [ ! -d $HILBERT_CLI_PATH/STATIONS ]; then
>&2 echo "STATIONS directory not found in the hilbert-cli path"
exit 1
fi

if [ ! -f $HILBERT_CLI_PATH/STATIONS/list ]; then
>&2 echo "STATIONS/list not found in the hilbert-cli path"
exit 1
fi

print_station()
{
  station_name=$1

  unset station_id
  unset station_type
  unset CFG_DIR
  unset background_services
  unset default_app
  unset possible_apps
  unset DM

  if [ ! -d $HILBERT_CLI_PATH/STATIONS/$station_name ]; then
  >&2 echo "Station directory STATIONS/$station_name not found in the hilbert-cli path"
  exit 1
  fi

  if [ ! -f $HILBERT_CLI_PATH/STATIONS/$station_name/station.cfg ]; then
  >&2 echo "Station configuration STATIONS/$station_name/station.cfg not found in the hilbert-cli path"
  exit 1
  fi

  if [ ! -f $HILBERT_CLI_PATH/STATIONS/$station_name/startup.cfg ]; then
  >&2 echo "Station configuration STATIONS/$station_name/startup.cfg not found in the hilbert-cli path"
  exit 1
  fi

  source $HILBERT_CLI_PATH/STATIONS/$station_name/station.cfg
  source $HILBERT_CLI_PATH/STATIONS/$station_name/startup.cfg

  echo "{"
  echo "\"id\": \"$station_id\","
  echo "\"name\": \"$station_name\","
  echo "\"type\": \"$station_type\","
#  echo "\"cfg_dir\": \"$CFG_DIR\","
#  echo "\"background_services\": \"$background_services\","
  echo "\"default_app\": \"$default_app\","

  echo "\"possible_apps\": ["
  local first=1
  for possible_app in $possible_apps; do
    if [ "$first" -eq "1" ]; then
      first=0
    else
      echo ","
    fi
    echo -n "\"$possible_app\""
  done
  echo ""
  echo "]"

#  echo "\"DM\": \"$DM\""
  echo "}"

  unset station_id
  unset station_type
  unset CFG_DIR
  unset background_services
  unset default_app
  unset possible_apps
  unset DM
}

echo "["

first=1
for station_name in $(cat $HILBERT_CLI_PATH/STATIONS/list | grep -v -E '^ *(#.*)? *$') ; do
  if [ "$first" -eq "1" ]; then
    first=0
  else
    echo ","
  fi
  print_station $station_name
done

echo "]"