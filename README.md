# Hilbert server & client CLI tools

Travis CI Build Status: [![devel](https://travis-ci.org/hilbert/hilbert-cli.svg?branch=devel)](https://travis-ci.org/hilbert/hilbert-cli)

## General System Overview

![System structure](docs/GeneralDD.png)

## General Hilbert Configuration model

![Configuration Model](docs/ConfigurationDD.png)

# General notes about shell scripts:

* Exit codes may be as follows:
  * 0: success
  * 1: detected error which is not our fault (e.g. network / HW etc): user can try again
  * 2: error due to wrong usage of scripts / in config files or some assumption was violated. 
  * other positive values: something unexpected has happened.

* One may need to capture both `STDOUT` and `STDERR`. Error messages (in `STDERR`) that are meant to be presented to users (admins) must be as informative as possible.

# Server-side low-level management CLI tool:

```
usage: hilbert [-h] [-p] [-t] [-d] [-V] [-v | -q] [-H] subcommand

Hilbert - server tool: loads configuration and does something using it

positional arguments:
 subcommand      :
                 app_change         change station's top application
                 app_restart        restart current/default application on a station
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
                 reboot             reboot station
                 run_shell_cmd      run specified shell command on given station...

optional arguments:
 -h, --help      show this help message and exit
 -p, --pedantic  turn on pedantic mode
 -t, --trace     turn on remote verbose-trace mode
 -d, --dryrun    increase dry-run mode
 -V, --version   show hilbert's version and exit
 -v, --verbose   increase verbosity
 -q, --quiet     decrease verbosity
 -H, --helpall   show detailed help and exit
```

# Client-side low-level driver (accessible either locally or via SSH):

```
usage: hilbert-station [-v|-q|-s] [-d|-D] [-t|-T] [-L] [-i|-h|-V|subcommand] [sub-arguments/options]

Hilbert - client part for Linux systems

positional arguments:
 subcommands:
   init [<cfg>]            init station based on given or installed configuration
   list_applications       list of (supported) applications
   list_services           list of background services
   app_change <app_id>     change the currently running top application to specified
   start [app_id]          start Hilbert on the system
   stop                    stop Hilbert on the system
   shutdown                shut down the system

optional arguments:
  -h                       show this help message [+internal commands/call tree, depending on verbosity] and exit
  -V                       show tool version [+internal info in verbose mode] and exit
  -i                       show internal info and exit
  -v                       increase verbosity
  -q                       decrease verbosity
  -s                       silent: minimal verbosity
  -t                       turn on BASH tracing and verbosity
  -T                       turn off BASH tracing and verbosity
  -d                       turn on dry-run mode
  -D                       turn off dry-run mode
  -L                       disable locking (e.g. for recursive sub-calls)

respected environment variables:
  HILBERT_CONFIG_BASEDIR   base configuration directory. Current: [~/.config/hilbert-station]
  HILBERT_CONFIG_DIR       configuration directory. Current: [~/.config/hilbert-station/configs]
  HILBERT_CONFIG_FILE      station config file. Current: [station.cfg]

currently detected hilbert variables/values: 
  HILBERT_SERVER_CONFIG_PATH: ...
  HILBERT_CONFIG_BACKUP: ~/.config/hilbert-station/config_backup
  HILBERT_SHUTDOWN_DELAY: 1s
  HILBERT_LOCKFILE_DIR: /var/run/hilbert
  HILBERT_STATION: .../bin/hilbert-station
```

NOTE: all commands (except `init <cfg>` / `shutdown` / `-h` / `-V`) require station's configuration to be present


## License
This project is licensed under the [Apache v2 license](LICENSE). See also [Notice](NOTICE).


