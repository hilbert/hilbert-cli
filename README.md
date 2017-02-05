# Hilbert server & client CLI tools

Travis CI Build Status: [![devel](https://travis-ci.org/hilbert/hilbert-cli.svg?branch=devel)](https://travis-ci.org/hilbert/hilbert-cli)

## General System Overview

![System structure](docs/GeneralDD.png)

## General Hilbert Configuration model

![Configuration Model](docs/ConfigurationDD.png)

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

# Server-side low-level management CLI tool:

```
usage: hilbert [-h] [-p] [-V] [-v | -q] [-H] subcommand

Hilbert - server tool: loads configuration and does something using it

positional arguments:
 subcommand      :
                 app_change         change station's top application
                 cfg_deploy         deploy station's local configuration to corresponding host
                 cfg_query          query some part of configuration. possibly dump it to a file
                 cfg_verify         verify the correctness of Hilbert Configuration .YAML file
                 list_applications  list application IDs
                 list_groups        list (named) group IDs
                 list_profiles      list profile IDs
                 list_services      list service IDs
                 list_stations      list station IDs
                 poweroff           finalize Hilbert on a station and shut it down
                 poweron            wake-up/power-on/start station

optional arguments:
 -h, --help      show this help message and exit
 -p, --pedantic  turn on pedantic mode
 -V, --version   show hilbert's version and exit
 -v, --verbose   increase verbosity
 -q, --quiet     decrease verbosity
 -H, --helpall   show detailed help and exit

```

# Client-side low-level driver (accessible either locally or via SSH):


```
usage: hilbert-station [-h] [-p] [-V] [-v | -q] subcommand

Hilbert - client part for Linux systems

positional arguments:
 subcommand:
   init [<cfg>]            init station based on given or installed configuration
   list_applications       list of (supported) applications
   list_services           list of background services
   app_change <app_id>     change the currently running top application to specified
   start                   start Hilbert on the system
   stop                    stop Hilbert on the system
   shutdown                shut down the system

optional arguments:
  -h                       show this help message and exit
  -V                       show version info and exit
  -v                       increase verbosity
  -q                       decrease verbosity
  -t                       turn on BASH tracing and verbosity
  -T                       turn off BASH tracing and verbosity
  -d                       turn on dry-run mode
  -D                       turn off dry-run mode

respected environment variables:
  HILBERT_CONFIG_BASEDIR   location of the base configuration directory of hilbert-station. Default: '~/.config/hilbert-station'
```

NOTE: all commands (except `init <cfg>` / `shutdown` / `-h` / `-V`) require station's configuration to be present

## License
This project is licensed under the [Apache v2 license](LICENSE). See also [Notice](NOTICE).
