# How-To guides for Hilbert system

Note: on a server "${HILBERT_SERVER_CONFIG_PATH}" should be equal to "/shared/interactives/0000_general/Hilbert/CFG/"

## Add a new PC into a hilbert setup

1. fix a DNS name (KIOSK_ADDRESS) for a new station (e.g. `kiosk023XXX.ads.eso.org`)
2. decide on proper <STATION_ID> for it (according to the following schema: `client_[0-9][0-9][0-9][0-9](_[0-9])?`)
3. depending on its HW decide on corresponding profile (i.e. set of services) to run on PC by default
4. add it into OMD (see below)
5. add it into `/shared/interactives/0000_general/Hilbert/CFG/Hilbert.yml` configuration
   * by analogy with existing stations but with its own unique networking and MAC addresses!
6. restart the Dashboard

## Add a station into OMD

Note: OMD Login credentials are present in other document with secrets

Let us add a station with ID: `<STATION_ID>` and network address: `<KIOSK_ADDRESS>`

NOTE: make sure that station is running Hilbert already (in order to discover all available CheckMK services on it) 

Create new host entry via: http://es-ex.hq.eso.org/default/check_mk/wato.py?mode=newhost&folder=

1. `Hostname` set to be `<STATION_ID>`
2. check `IP address` and set input field to be `<KIOSK_ADDRESS>`
3. press bottom-left button: "Save and go to serrvices"
4. on "Services of host `<STATION_ID>` (might be cached data)" there should be around 20 services (most of them should be green)
5. press button "Automatic Refresh (Tabula Rasa)"

After you are done adding all stations go to top button "... Changes": http://es-ex.hq.eso.org/default/check_mk/wato.py?mode=changelog&folder=
and press button "Activate Changes!"

Result should be:

```
Progress	Status
OK              Configuration successfully activated.
```

## Check Hilbert configuration and docker-compose files

Run the following on your current server:
```
$ cd /shared/interactives/0000_general/Hilbert/CFG
$ ./check_cfg.sh
```

## Deployment of Hilbert configuration to specified station (or refresh/update Hilbert there)

Run the following on your current server:
```
$ cd /shared/interactives/0000_general/Hilbert/CFG
$ ./hilbert cfg_deploy <STATION_ID>
```

Note: on remote station Hilbert configuration will by installed under `~/.config/hilbert-station/` by default. 
Only Hilbert client-side CLI tool `hilbert-station` is supposed to work with it.


## Cleanup remote station

Run the following on your current server:

```
$ cd /shared/interactives/0000_general/Hilbert/CFG
$ ./hilbert cleanup <STATION_ID>
```

Alternatively after logging-in to corresponding host (via `hilbert-ssh <STATION_ID>` or `ssh <KIOSK_ADDRESS>`) via ssh run the following:
```
$ hilbert-station cleanup # or
$ hilbert-station cleanup --force # if Hilbert is currently running
```



## Hilbert client-side CLI tool: `hilbert-station`

```
usage: hilbert-station [-v|-q|-s] [-d|-D] [-t|-T] [-L] [-i|-h|-V|subcommand] [sub-arguments/options]

Hilbert - client part for Linux systems

positional arguments:
 subcommands:
   init [<cfg>]             init station based on given or installed configuration
   list_applications        list of (supported) applications
   list_services            list of background services
   app_change <app_id>      change the currently running top application to specified
   app_restart              restart the currently running top application
   start [<app_id>]         start Hilbert on the system
   pause                    pause Hilbert on the system
   stop                     stop Hilbert on the system
   shutdown [now]           shut down the system
   reboot [now]             reboot the system
   cleanup [--force]        local system cleanup (identical to docker_cleanup on Linux host)
   docker_cleanup [--force] total cleanup of local docker engine (images, data volumes)

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
```

Note: `hilbert-station` is a bash script installed on station via `hilbert-cli-*.rpm`.
Its source is available at https://github.com/hilbert/hilbert-cli/ (in `tools/hilbert-station`)



## Hilbert server-side CLI tool

```
$ hilbert
usage: hilbert [-h] [-p] [-t] [-d] [-V] [-v | -q] [-H] subcommand

Hilbert - server tool: loads configuration and does something using it

positional arguments:
 subcommand      :
                 app_change         change station's top application
                 app_restart        restart current/default application on a station
                 cfg_deploy         deploy station's local configuration to corresponding host
                 cfg_query          query some part of configuration. possibly dump it to a file
                 cfg_verify         verify the correctness of Hilbert Configuration .YAML file
                 cleanup            perform system cleanup on remote station
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

Run `hilbert -H` for detailed information on all commands

Note: `hilbert` is a CLI packaged Python script. Its sources are available at https://github.com/hilbert/hilbert-cli


## Hilbert Data/Configuration Restoration for a server

See also `/shared/server.backup_restore/README.md` for more details

Note: the procedure will take quite a long time therefore it is better to run it 
within some terminal multiplexer (e.g. `screen` or `tmux`) so that it will not be interrupted 
if your connection to server is cut. 

Suggested procedure:

1. login as `kiosk` user to new (empty) server
2. check that NFS mounted disk `/shared` is present
3. run `tmux` (or `screen`): should start another shell line, where you run the following command:
4. run `/shared/server.backup_restore/bin/restore.sh`

NOTE: Please do not use `Ctrl+C` to exit. 
Use `Crtl+b d` or `Ctrl+a d` to detach from multiplexer session. 
Later on you can attach back to previous session with `tmux at` after logging to the server.

NOTE: do not use `root` for restoration!
