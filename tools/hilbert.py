#! /usr/bin/env python

# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

# PYTHON_ARGCOMPLETE_OK           # NOQA

from __future__ import absolute_import, print_function, unicode_literals
import argparse  # NOQA
import logging
import sys
import os
from os import path

DIR = path.dirname(path.dirname(path.abspath(__file__)))
if path.exists(path.join(DIR, 'hilbert_config', 'hilbert_cli_config.py')):
    sys.path.append(DIR)
    sys.path.append(path.join(DIR, 'hilbert_config'))
    from helpers import *
    from hilbert_cli_config import *
    from subcmdparser import *
else:
    from hilbert_config.hilbert_cli_config import *
    from hilbert_config.helpers import *
    from hilbert_config.subcmdparser import *

# datefmt='%Y.%m.%d %I:%M:%S %p'
logging.basicConfig(format='%(levelname)s  [%(filename)s:%(lineno)d]: %(message)s')
# %(name)s            Name of the logger (logging channel)
# %(levelno)s         Numeric logging level for the message (DEBUG, INFO, WARNING, ERROR, CRITICAL)
# %(levelname)s       Text logging level for the message ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")
# %(pathname)s        Full pathname of the source file where the logging call was issued (if available)
# %(filename)s        Filename portion of pathname
# %(module)s          Module (name portion of filename)
# %(lineno)d          Source line number where the logging call was issued (if available)
# %(funcName)s        Function name
# %(created)f         Time when the LogRecord was created (time.time() return value)
# %(asctime)s         Textual time when the LogRecord was created
# %(msecs)d           Millisecond portion of the creation time
# %(relativeCreated)d Time in milliseconds when the LogRecord was created,
#                     relative to the time the logging module was loaded
#                     (typically at application startup time)
# %(thread)d          Thread ID (if available)
# %(threadName)s      Thread name (if available)
# %(process)d         Process ID (if available)
# %(message)s         The result of record.getMessage(), computed just as the record is emitted

log = logging.getLogger(__name__)  #

__CLI_VERSION_ID = "$Id$"


# import traceback
# def main_exception_handler(type, value, tb):
#    log.exception("Uncaught exception! Type: {0}, Value: {1}, TB: {2}".format(type, value, traceback.format_tb(tb)))
##sys.excepthook = main_exception_handler # Install exception handler


def set_log_level_options(_ctx):
    if 'verbose' in _ctx:
        c = _ctx['verbose']
        if c is None:
            c = 0
        for i in range(c):
            add_HILBERT_STATION_OPTIONS('-v')

    if 'quiet' in _ctx:
        c = _ctx['quiet']
        if c is None:
            c = 0
        for i in range(c):
            add_HILBERT_STATION_OPTIONS('-q')



@subcmd('cfg_verify', help='verify the correctness of Hilbert Configuration .YAML file')
def cmd_verify(parser, context, args):
    log.debug("Running '{}'".format('cfg_verify'))

    # TODO: optional due to default value?
    parser.add_argument('configfile', help="input .YAML file, default: 'Hilbert.yml'", nargs='?')

    args = parser.parse_args(args)
    cfg = input_handler(parser, vars(context), args)

    if cfg is not None:
        print("Input is a valid Hilbert configuration!")
    else:
        print("Input seems to be invalid Hilbert configuration!")
        sys.exit(1)

    return args


def input_handler(parser, ctx, args):
    fn = None
    df = None

    args = vars(args)

    if 'configfile' in args:
        fn = args['configfile']
        log.debug("Input YAML file specified: {}".format(fn))

    if 'configdump' in args:
        df = args['configdump']
        log.debug("Input dump file specified: {}".format(df))

    if (fn is None) and (df is None):
        fn = os.environ.get('HILBERT_SERVER_CONFIG_PATH', None)
        if fn is not None:
            if os.path.isdir(fn):
                fn = os.path.join(fn, 'Hilbert.yml')
            log.info("Missing input file specification: using $HILBERT_SERVER_CONFIG_PATH: '{}'!".format(fn))
        else:
            fn = os.path.join('.', 'Hilbert.yml')
            log.info("Missing input file specification: using default: '{}'!".format(fn))

    if (fn is not None) and (df is not None):
        log.error("Input file specification clashes with the input dump specification: specify a single input source!")
        sys.exit(1)

    if fn is not None:
        if not URI(None).validate(fn):
            log.error("Wrong file specification: '{}'".format(fn))
            sys.exit(1)
        log.info("Input file: '{}'".format(fn))

    if df is not None:
        if not URI(None).validate(fn):
            log.error("Wrong dump file specification: '{}'".format(df))
            sys.exit(1)
        log.info("Input dump file: '{}'".format(df))

    if fn is not None:
        set_INPUT_DIRNAME(path.abspath(path.dirname(fn)))
    else:
        assert df is not None
        set_INPUT_DIRNAME(path.abspath(path.dirname(df)))

    cfg = None

    if fn is not None:
        log.info("Loading '{}'...".format(fn))
        try:
            yml = load_yaml_file(fn)
            log.info("Input file is a correct YAML!")

            log.info("Data Validation/Parsing: ")

            os.chdir(get_INPUT_DIRNAME())  # NOTE: references relative to input file's location!
            cfg = parse_hilbert(yml)  # NOTE: checks that this is a proper dictionary...
        except:
            log.exception("ERROR: wrong input file: '{}'!".format(fn))
            sys.exit(1)
    else:
        log.info("Loading dump '{}'...".format(df))
        try:
            cfg = pickle_load(df)
            log.info("Input dump file is valid!")
        except:
            log.exception("Wrong input dump file: '{}'!".format(df))
            sys.exit(1)

    if cfg is None:
        log.error("Could not get the configuration!")
        sys.exit(1)

    assert isinstance(cfg, Hilbert)
    log.info("Configuration is OK!")

    return cfg


###############################################################################
def output_handler(parser, ctx, args):
    args = vars(args)

    od = None
    if 'outputdump' in args:
        od = args['outputdump']
        log.debug("Specified output dump file: {}".format(od))
        assert od is not None

        f = URI(None)
        if f.validate(od):
            if os.path.exists(f.get_data()):  # TODO: testme!
                if not get_PEDANTIC():
                    log.warning("Output dump file: '{}' already exists! Will be overwritten!".format(od))
                else:
                    log.warning(
                        "Output dump file: '{}' already exists! Cannot overwrite it in PEDANTIC mode!".format(od))
                    od = None
        else:  # TODO: testme!
            log.error("Wrong output file: '{}'".format(od))
            od = None
    return od


def cmd_list(parser, context, args, obj):
    cfg = input_handler(parser, vars(context), args)
    return cfg.query(obj)


@subcmd('cfg_query', help='query some part of configuration. possibly dump it to a file')
def cmd_query(parser, context, args):
    log.debug("Running '{}'".format('cfg_query'))

    parser.add_argument('-o', '--object', required=False, default='all',
                        help="specify the object in the config (default: 'all')")
    parser.add_argument('-od', '--outputdump', default=argparse.SUPPRESS,
                        help="specify output dump file")

    group = parser.add_mutually_exclusive_group(required=False)

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")  # NOTE: default!
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    args = parser.parse_args(args)

    _args = vars(args)

    obj = 'all'
    if 'object' in _args:
        obj = _args['object']

    try:
        log.info("Querring object: '{}'... ".format(obj))
        obj = cmd_list(parser, context, args, obj)
    except:
        log.exception("Sorry cannot query '{}' yet!".format(obj))
        sys.exit(1)

    assert obj is not None

    if isinstance(obj, BaseValidator):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    od = output_handler(parser, vars(context), args)

    if od is not None:
        log.info("Writing the configuration into '{}'...".format(od))
        pickle_dump(od, obj)

    return args


@subcmd('list_applications', help='list application IDs')
def cmd_list_applications(parser, context, args):
    log.debug("Running '{}'".format('list_applications'))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    args = parser.parse_args(args)

    log.debug("Listing all Application ID...")

    obj = None
    try:
        obj = cmd_list(parser, context, args, 'Applications/keys')
    except:
        log.exception("Sorry could not get the list of '{}' from the input file!".format('applications'))
        sys.exit(1)

    assert obj is not None

    if isinstance(obj, BaseValidator):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    return args


@subcmd('list_stations', help='list station IDs')
def cmd_list_stations(parser, context, args):
    log.debug("Running '{}'".format('list_stations'))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    parser.add_argument('-f', '--format', choices=['list', 'dashboard'],
                        default='list', required=False,
                        help="output format")

    args = parser.parse_args(args)

    _args = vars(args)

    mode = _args.get('format', 'list')

    if mode == "list":
        log.debug("Listing all Station ID...")

        obj = None
        try:
            obj = cmd_list(parser, context, args, 'Stations/keys')
        except:
            log.exception("Sorry could not get the list of '{}' from the input file!".format('stations'))
            sys.exit(1)

        assert obj is not None

        if isinstance(obj, BaseValidator):
            print(yaml_dump(obj.data_dump()))
        else:
            print(yaml_dump(obj))
    else:
        assert mode == 'dashboard'

        log.debug("Loading/parsing configuration...")
        cfg = input_handler(parser, vars(context), args)
        assert cfg is not None
        assert isinstance(cfg, Hilbert)

        obj = None
        log.debug("Listing all Stations for Dashboard...")
        try:
            obj = cfg.query('Stations/data')
        except:
            log.exception("Sorry could not query Stations's details from the given configuration!")
            sys.exit(1)

        assert obj is not None
        if isinstance(obj, BaseValidator):
            obj = obj.data_dump()

        first = True
        print('[')
        for k in obj:
            o = obj.get(k, None)
            assert o is not None

            if (o.get('hidden', '') == 'true') or (o.get('hidden', False) == True):
                continue

            assert 'name' in o
            assert 'profile' in o

            s = o.get('client_settings', None)
            d = ''
            if s is not None:
                assert isinstance(s, dict)
                d = s.get('hilbert_station_default_application', '')

            assert 'compatible_applications' in o
            apps = None
            try:
                apps = o.get('compatible_applications', None)
            except:
                log.exception("Sorry could not query compatible_applications for a station [%s]!", k)
                sys.exit(1)

            if isinstance(apps, BaseValidator):
                apps = apps.data_dump()

            apps = '\n"' + '",\n"'.join(apps) + '"\n'

            if not first:
                print(',')

            print('{')
            print('"{0}": "{1}",'.format('id', k))
            print('"{0}": "{1}",'.format('name', o['name']))
            print('"{0}": "{1}",'.format('type', o['profile']))
            print('"{0}": "{1}",'.format('default_app', d))
            print('"{0}": [{1}]'.format('possible_apps', apps))
            print('}')

            first = False

        print(']')

    return args


@subcmd('list_profiles', help='list profile IDs')
def cmd_list_profiles(parser, context, args):
    log.debug("Running '{}'".format('list_profiles'))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    args = parser.parse_args(args)

    log.debug("Listing all Profile ID...")

    obj = None
    try:
        obj = cmd_list(parser, context, args, 'Profiles/keys')
    except:
        log.exception("Sorry could not get the list of '{}' from the input file!".format('profiles'))
        sys.exit(1)

    assert obj is not None

    if isinstance(obj, BaseValidator):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    return args


@subcmd('list_groups', help='list (named) group IDs')
def cmd_list_groups(parser, context, args):
    log.debug("Running '{}'".format('list_groups'))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    args = parser.parse_args(args)

    log.debug("Listing all Group ID...")

    obj = None
    try:
        obj = cmd_list(parser, context, args, 'Groups/keys')
    except:
        log.exception("Sorry could not get the list of '{}' from the input file!".format('groups'))
        sys.exit(1)

    assert obj is not None

    if isinstance(obj, BaseValidator):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    return args


@subcmd('list_services', help='list service IDs')
def cmd_list_services(parser, context, args):
    log.debug("Running '{}'".format('list_services'))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    args = parser.parse_args(args)

    log.debug("Listing all Service ID...")

    obj = None
    try:
        obj = cmd_list(parser, context, args, 'Services/keys')
    except:
        log.exception("Sorry could not get the list of '{}' from the input file!".format('services'))
        sys.exit(1)

    assert obj is not None

    if isinstance(obj, BaseValidator):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    return args

# NOTE: just a helper ATM
def cmd_action(parser, context, args, Action=None, appIdRequired=False):
    args = parser.parse_args(args)
    _args = vars(args)
    _ctx = vars(context)

    action = Action
    if action is None:
        assert 'Action' in _args
        action = _args['Action']

    log.debug("Action: '%s'", action)

    assert action is not None
    assert action != ''

    # stationId,
    assert 'StationID' in _args
    stationId = _args['StationID']
    log.debug("Input StationID: '%s'", stationId)
    stationId = StationID.parse(stationId, parent=None, parsed_result_is_data=True)
    log.debug("Checked StationID: '%s'", stationId)

    action_args = None

    if appIdRequired:
        applicationID = _args.get('ApplicationID', None)
        assert applicationID is not None
        log.debug("Input ApplicationID: '%s'", applicationID)
        applicationID = ApplicationID.parse(applicationID, parent=None, parsed_result_is_data=True)
        log.debug("Checked ApplicationID: '%s'", applicationID)
        action_args = applicationID

    elif 'action_args' in _args:
        action_args = _args.get('action_args', None)


    stations = None
    log.debug("Validating given StationID: '%s'...", stationId)
    try:
        log.debug("Querying all stations in the Configuration...")
        stations = cmd_list(parser, context, args, 'Stations/all')
    except:
        log.exception("Sorry could not get the list of '{}' from the input file!".format('stations'))
        sys.exit(1)

    assert stations is not None

    if stationId not in stations.get_data():
        log.error("Invalid StationID (%s)!", stationId)
        print()
        sys.exit(1)

    station = stations.get_data()[stationId]
    assert station is not None

    log.debug("StationID is valid according to the Configuration!")
    log.debug("Running action: '{0} {1}' on station '{2}'".format(action, str(action_args), stationId))

    set_log_level_options(_ctx)

    try:
        station.run_action(action, action_args)  # NOTE: temporary API for now
    except:
        log.exception("Could not run '{0} {1}' on station '{2}'".format(action, str(action_args), stationId))
        sys.exit(1)
    return args


@subcmd('poweron', help='wake-up/power-on/start station')
def cmd_start(parser, context, args):
    action = 'start'
    log.debug("Running 'cmd_{}'".format(action))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    parser.add_argument('StationID', help="station to power-on via network")
    #    parser.add_argument('action_args', nargs='?', help="optional arguments for poweron", metavar='args')

    cmd_action(parser, context, args, Action=action, appIdRequired=False)

    return args


@subcmd('poweroff', help='finalize Hilbert on a station and shut it down')
def cmd_stop(parser, context, args):
    action = 'stop'
    log.debug("Running 'cmd_{}'".format(action))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    parser.add_argument('StationID', help="specify the station")
    #    parser.add_argument('action_args', nargs='?', help="optional arguments for shutdown", metavar='args')

    cmd_action(parser, context, args, Action=action, appIdRequired=False)

    return args


@subcmd('cfg_deploy', help="deploy station's local configuration to corresponding host")
def cmd_cfg_deploy(parser, context, args):
    action = 'cfg_deploy'
    log.debug("Running 'cmd_{}'".format(action))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    parser.add_argument('StationID', help="specify the station")
    #    parser.add_argument('action_args', nargs='?', help="optional arguments for deploy", metavar='args')

    cmd_action(parser, context, args, Action=action, appIdRequired=False)

    return args


# @subcmd('app_start', help='start an application on a station')
def cmd_app_start(parser, context, args):
    action = 'app_start'
    log.debug("Running 'cmd_{}'".format(action))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    parser.add_argument('StationID', help="specify the station")
    parser.add_argument('ApplicationID', help="specify the application to start")
    #    parser.add_argument('action_args', nargs='?', help="optional argument for start: ApplicationID/ServiceID ", metavar='id')

    cmd_action(parser, context, args, Action=action, appIdRequired=True)

    return args


# @subcmd('app_stop', help='stop the current application on a station')
def cmd_app_stop(parser, context, args):
    action = 'app_stop'
    log.debug("Running 'cmd_{}'".format(action))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    parser.add_argument('StationID', help="specify the station")
    #    parser.add_argument('ApplicationID', help="specify the application to stop")
    #    parser.add_argument('action_args', nargs='?',
    #              help="optional argument for finish: ApplicationID/ServiceID ", metavar='id')

    cmd_action(parser, context, args, Action=action, appIdRequired=True)

    return args


@subcmd('app_change', help="change station's top application")
def cmd_app_change(parser, context, args):
    action = 'app_change'
    log.debug("Running 'cmd_{}'".format(action))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    parser.add_argument('StationID', help="specify the station")
    parser.add_argument('ApplicationID', help="new top Application")
    #    parser.add_argument('other_args', nargs='?', help="optional arguments for 'app_change'", metavar='args')

    cmd_action(parser, context, args, Action=action, appIdRequired=True)

    return args

@subcmd('ssh', help="connect to a station via SSH")
def cmd_ssh(parser, context, args):
    action = 'ssh'
    log.debug("Running 'cmd_{}'".format(action))

    group = parser.add_mutually_exclusive_group()

    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    parser.add_argument('StationID', help="specify the station")

    cmd_action(parser, context, args, Action=action, appIdRequired=False)

    return args

# @subcmd('run_action', help='run specified action on given station with given arguments...')
def cmd_run_action(parser, context, args):
    log.debug("Running 'cmd_{}'".format('run_action'))

    group = parser.add_mutually_exclusive_group()
    group.add_argument('--configfile', required=False,
                       help="specify input .YAML file (default: 'Hilbert.yml')")
    group.add_argument('--configdump', required=False,
                       help="specify input dump file")

    parser.add_argument('Action', help="specify the action")
    parser.add_argument('StationID', help="specify the station")
    parser.add_argument('action_args', nargs='?', help="optional arguments for the action", metavar='args')

    cmd_action(parser, context, args, Action=None, appIdRequired=False)

    return args


class PedanticModeAction(argparse._StoreTrueAction):
    def __init__(self, *args, **kwargs):
        super(PedanticModeAction, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super(PedanticModeAction, self).__call__(*args, **kwargs)
        start_pedantic_mode()


class RemoteTraceModeAction(argparse._StoreTrueAction):
    def __init__(self, *args, **kwargs):
        super(RemoteTraceModeAction, self).__init__(*args, **kwargs)

    def __call__(self, *args, **kwargs):
        super(RemoteTraceModeAction, self).__call__(*args, **kwargs)
        add_HILBERT_STATION_OPTIONS('-t')


class CountedDryRunModeAction(argparse._CountAction):
    def __init__(self, *args, **kwargs):
        super(CountedDryRunModeAction, self).__init__(*args, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        new_count = argparse._ensure_value(namespace, self.dest, 0) + 1
        setattr(namespace, self.dest, new_count)

        start_dry_run_mode()  # increase


def _version():
    import platform
    import dill
    import ruamel.yaml as yaml
    import semantic_version

    log.debug("Running '--{}'".format('version'))

    log.debug("Python (platform) version: {}".format(platform.python_version()))
    log.debug("ruamel.yaml       version: {}".format(yaml.__version__))
    log.debug("dill              version: {}".format(dill.__version__))
    log.debug("logging           version: {}".format(logging.__version__))
    log.debug("semantic_version  version: {}".format(semantic_version.__version__))

    print("Hilbert Configuration API:     {}".format(Hilbert(None).get_api_version()))
    print("Root Logging Level:            {}".format(logging.getLevelName(logging.getLogger().level)))
    print("PEDANTIC mode:                 {}".format(get_PEDANTIC()))
    print("DRY_RUN mode:                  {}".format(get_DRY_RUN_MODE()))
    print("HILBERT_STATION_OPTIONS:       {}".format(get_HILBERT_STATION_OPTIONS()))

    d = os.environ.get('HILBERT_SERVER_CONFIG_PATH', None)
    if d is not None:
        print("HILBERT_SERVER_CONFIG_PATH:  {}".format(d))

    d = os.environ.get('HILBERT_SERVER_CONFIG_SSH_PATH', None)
    if d is not None:
        print("HILBERT_SERVER_CONFIG_SSH_PATH:  {}".format(d))


# print("INPUT_DIRNAME:                 {}".format(get_INPUT_DIRNAME()))


class ListVersionsAction(argparse._VersionAction):
    def __init__(self, option_strings, *args, **kwargs):
        super(ListVersionsAction, self).__init__(option_strings=option_strings, *args, **kwargs)

    def __call__(self, parser, args, values, option_string=None):
        set_log_level_options(vars(args))
#        formatter = parser._get_formatter()
#        formatter.add_text(version)
#        parser._print_message(formatter.format_help(), _sys.stdout)
        _version()
        parser.exit()

def main():
    handler = SubCommandHandler(use_subcommand_help=True, enable_autocompletion=True,
                                prog='hilbert',
                                description="Hilbert - server tool: loads configuration and does something using it")

    handler.add_argument('-p', '--pedantic', action=PedanticModeAction,
                         default=argparse.SUPPRESS, required=False,
                         help="turn on pedantic mode")

    handler.add_argument('-t', '--trace', action=RemoteTraceModeAction,
                         default=argparse.SUPPRESS, required=False,
                         help="turn on remote verbose-trace mode")

    handler.add_argument('-d', '--dryrun', action=CountedDryRunModeAction,
                         help="increase dry-run mode")

    handler.add_argument('-V', '--version', action=ListVersionsAction,
                         help="show %(prog)s's version and exit")
    #              nargs=0, default=argparse.SUPPRESS, required=False, type=None, metavar=None,


    _argv = sys.argv[1:]

    # NOTE: show help by if not arguments given
    if len(_argv) == 0:
        log.debug("No command arguments given => Showing usage help!")
        _argv = ['-h']
    # handler.print_help()

    args = handler.run(_argv)
    handler.exit()


if __name__ == "__main__":
    main()
