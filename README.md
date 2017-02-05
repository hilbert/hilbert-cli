# Hilbert server & client CLI tools

[![Build Status: master](https://travis-ci.org/hilbert/hilbert-cli.svg?branch=master)](https://travis-ci.org/hilbert/hilbert-cli)
[![devel](https://travis-ci.org/hilbert/hilbert-cli.svg?branch=devel)](https://travis-ci.org/hilbert/hilbert-cli)
[![Current PR](https://travis-ci.org/hilbert/hilbert-cli.svg?branch=feature/hilbert_cli_tools)](https://travis-ci.org/hilbert/hilbert-cli)

## General System Overview

![System structure](docs/GeneralDD.png)

## Distilled `Hilbert` interfaces/interactions:

![Minimal `hilbert` interfaces](docs/HilbertDD.png)

## Current management structure:

![Detailed current management structure](docs/mng.png)

# General notes about shell scripts:

* Exit codes may be as follows (see `status.sh`, others will be updated):
  * 0: success
  * 1: detected error which is not our fault (e.g. network / HW etc): user can try again
  * 2: error due to wrong usage of scripts / in config files or some assumption was violated. 
  * other positive values: something unexpected has happened.

* One may need to capture both `STDOUT` and `STDERR`. Error messages (in `STDERR`) that are meant to be presented to users (admins) must be as informative as possible.

# UI Back-end: high-level action scripts

* `list_stations.sh`: query current YAML configuration (`hilbert list_stations --format dashboard`)
* `start_station.sh`: start stopped station (`hilbert poweron $station_id`)
  1. initiates station power-on (e.g. via WOL)
* `appchange_station.sh`: switch GUI applicaiton running on the station `hilbert app_change $station_id $app_id`
  1. switch GUI app. on the station
* `stop_station.sh`: stop station (`hilbert poweroff $station_id`):
  1. gracefully finish (stop / kill / remove) all running framework' services 
  2. initiate system shutdown (with power-off) of the station (alternative: `poweroff.sh $station_id`)

NOTE: rebooting the station can be done with: `shutdown.sh STATION -r now` or `reboot.sh STATION`

TODOs: 
  * `sync.sh` (to synchronize local cache `STATIONS/` with station configs & scripts from CMS). 
  Sync. is to be performed once before front-end starts & upon request from CMS (external trigger!):
  * `start_station.sh` will not wait for remote machine to power-on completely - there should be a wait on OMD afterwards
  * `stop_station.sh` and `appchange_station.sh` should trigger update of OMD checks

# Server-side low-level management commands: see `hilbert -h`

# Station-side low-level commands (accessible either locally or via SSH): see `hilbert-station -h`

NOTE: some of the actions may require station's configuration (e.g. in  `~/.config/hilbert-station/`)


## License
This project is licensed under the [Apache v2 license](LICENSE). See also [Notice](NOTICE).
