#!/usr/bin/env python2

# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

assert __name__ == "__main__"

import sys
from os import path
DIR=path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(path.join(DIR, 'config'))

from helpers import *
from hilbert_cli_config import *

#from config.hilbert_cli_config import *
#from config.helpers import *

from arghandler import *               # NOQA 
import argparse                        # NOQA

import logging
log = logging.getLogger(__name__)  #

# level=logging.INFO!!! , datefmt='%Y.%m.%d %I:%M:%S %p'
logging.basicConfig(format='%(levelname)s [%(filename)s:%(lineno)d]: %(message)s', level=logging.DEBUG)
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
# %(relativeCreated)d Time in milliseconds when the LogRecord was created, relative to the time the logging module was loaded
#                     (typically at application startup time)
# %(thread)d          Thread ID (if available)
# %(threadName)s      Thread name (if available)
# %(process)d         Process ID (if available)
# %(message)s         The result of record.getMessage(), computed just as the record is emitted
import traceback
def main_exception_handler(type, value, tb):
    log.exception("Uncaught exception! Type: {0}, Value: {1}, TB: {2}".format(type, value, traceback.format_tb(tb)))

# sys.excepthook = main_exception_handler # Install exception handler

def _version():
    import platform
    import dill
    import ruamel.yaml as yaml
    import semantic_version
    log.info("Python           version: {}".format(platform.python_version()))
    log.info("ruamel.yaml      version: {}".format(yaml.__version__))
    log.info("dill             version: {}".format(dill.__version__))
    log.info("semantic_version version: {}".format(semantic_version.__version__))
#    log.info("Hilbert.Config   version: {}".format(config.__version__))  # TODO!

    # arghandler version? dill version? etc?


def _load(f):
    return load_yaml_file(f)  # TODO: check that this is a dictionary!


@subcmd('version', help='Display version info')
def cmd_version(parser, context, args):
    log.debug("Running '{}'".format('cfg_version'))
    _version()
    log.debug("Done")
    exit(0)


@subcmd('cfg_verify', help='Check correctness of a given general Hilbert configuration (YAML) file as far as possible...')
def cmd_verify(parser, context, args):
    global PEDANTIC
    global INPUT_DIRNAME

    log.debug("Running '{}'".format('cfg_verify'))

    ctx = vars(context)
    pedantic_handler(parser, ctx, args)

    if 'inputdump' in ctx:
        df = ctx['inputdump']
        if df is not None:
            log.error("Sorry: cannot verify a dump file.")
            exit(1)

    args = parser.parse_args(args)
    cfg = input_handler(parser, ctx, args)

    log.debug("Done")
    exit(0)

def pedantic_handler(parser, ctx, args):
    global PEDANTIC

    if 'pedantic' in ctx:
        PEDANTIC = ctx['pedantic']

    if PEDANTIC:
        log.debug("PEDANTIC mode is ON!")

def input_handler(parser, ctx, args):
    global INPUT_DIRNAME

    fn = None
    df = None

    if 'inputfile' in ctx:
        fn = ctx['inputfile']
        log.debug("Input YAML file specified: {}".format(fn))

    if 'inputdump' in ctx:
        df = ctx['inputdump']
        log.debug("Input dump file specified: {}".format(df))

    if (fn is None) and (df is None):
        fn = 'Hilbert.yml'
        log.warning("Missing input file specification: using default '{}'!".format(fn))

    if (fn is not None) and (df is not None):
        log.error("Input file specification clashes with the input dump specification: specify a single input source!")
        exit(1)

    if fn is not None:
        if not URI(None).validate(fn):
            log.error("Wrong file specification: '{}'".format(fn))
            exit(1)
        log.info("Input file: '{}'".format(fn))

    if df is not None:
        if not URI(None).validate(fn):
            log.error("Wrong dump file specification: '{}'".format(df))
            exit(1)
        log.info("Input dump file: '{}'".format(df))

    if fn is not None:
        INPUT_DIRNAME = os.path.abspath(os.path.dirname(fn))
    else:
        assert df is not None
        INPUT_DIRNAME = os.path.abspath(os.path.dirname(df))

    cfg = None

    if fn is not None:
        log.info("Loading '{}'...".format(fn))
        try:
            yml = _load(fn)
            log.info("Input file is a valid YAML!")

            os.chdir(INPUT_DIRNAME)
            log.info("Data Validation/Parsing: ")

            cfg = parse_hilbert(yml)

        except:
            log.exception("ERROR: wrong input file: '{}'!".format(fn))
            exit(1)
    else:
        log.info("Loading dump '{}'...".format(df))
        try:
            cfg = pickle_load(df)
            log.info("Input dump file is valid!")
        except:
            log.exception("Wrong input dump file: '{}'!".format(df))
            exit(1)

    if cfg is None:
        log.error("Could not get the configuration!")
        exit(1)

    assert isinstance(cfg, Hilbert)
    log.info("Configuration is OK!")

    return cfg


def output_handler(parser, ctx, args):
    args = vars(args)

    od = None
    if 'outputdump' in args:
        od = args['outputdump']
        log.debug("Specified output dump file: {}".format(od))
        assert od is not None

        if URI(None).validate(od):
            if not PEDANTIC:
                log.warning("Output dump file: '{}' already exists! Will be overwritten!".format(od))
            else:
                log.warning("Output dump file: '{}' already exists! Cannot overwrite it in PEDANTIC mode!".format(od))
                od = None
    return od

def cmd_list(parser, context, args, obj):
    ctx = vars(context)
    pedantic_handler(parser, ctx, args)
    cfg = input_handler(parser, ctx, args)
    return cfg.query(obj)


@subcmd('cfg_query', help='Load Configuration and query some part of it')
def cmd_query(parser, context, args):
    log.debug("Running '{}'" . format('cfg_query'))

    parser.add_argument('-o', '--object', required=False, default='all',
            help="specify the object in the config (default: 'all')")
    parser.add_argument('-od', '--outputdump', default=argparse.SUPPRESS,
            help="specify output dump file")

    args = parser.parse_args(args)

    _args = vars(args)

    obj = 'all'
    if 'object' in _args:
        obj = _args['object']

    try:
        log.info("Querring object: '{}'... " . format(obj))
        obj = cmd_list(parser, context, args, obj)
    except:
        log.exception("Sorry cannot query '{}' yet!" . format(obj))
        exit(1)

    assert obj is not None

    if isinstance(obj, Base):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    od  = output_handler(parser, vars(context), args)

    if od is not None:
        log.info("Writing the configuration into '{}'...".format(od))
        pickle_dump(od, obj)

    log.debug("Done")
    exit(0)

@subcmd('list_applications', help='Load Configuration and list its applications')
def cmd_list_applications(parser, context, args):
    log.debug("Running '{}'" . format('list_applications'))
    log.debug("Listing all Application ID...")

    args = parser.parse_args(args)

    obj = None
    try:
        obj = cmd_list(parser, context, args, 'Applications/keys')
    except:
        log.exception("Sorry could not get the list of '{}' from the input file!".format('applications'))
        exit(1)

    assert obj is not None

    if isinstance(obj, Base):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    log.debug("Done")
    exit(0)

@subcmd('list_stations', help='Load Configuration and list its stations')
def cmd_list_stations(parser, context, args):
    log.debug("Running '{}'" . format('list_stations'))
    log.debug("Listing all Station ID...")

    args = parser.parse_args(args)

    obj = None
    try:
        obj = cmd_list(parser, context, args, 'Stations/keys')
    except:
        log.exception("Sorry could not get the list of '{}' from the input file!".format('stations'))
        exit(1)

    assert obj is not None

    if isinstance(obj, Base):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    log.debug("Done")
    exit(0)


@subcmd('list_profiles', help='Load Configuration and list its profiles')
def cmd_list_profiles(parser, context, args):
    log.debug("Running '{}'" . format('list_profiles'))
    log.debug("Listing all Profile ID...")

    args = parser.parse_args(args)

    obj = None
    try:
        obj = cmd_list(parser, context, args, 'Profiles/keys')
    except:
        log.exception("Sorry could not get the list of '{}' from the input file!".format('profiles'))
        exit(1)

    assert obj is not None

    if isinstance(obj, Base):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    log.debug("Done")
    exit(0)


@subcmd('list_groups', help='Load Configuration and list its named groups')
def cmd_list_groups(parser, context, args):
    log.debug("Running '{}'" . format('list_groups'))
    log.debug("Listing all Group ID...")

    args = parser.parse_args(args)

    obj = None
    try:
        obj = cmd_list(parser, context, args, 'Groups/keys')
    except:
        log.exception("Sorry could not get the list of '{}' from the input file!".format('groups'))
        exit(1)

    assert obj is not None

    if isinstance(obj, Base):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    log.debug("Done")
    exit(0)


@subcmd('list_services', help='Load Configuration and list its services')
def cmd_list_services(parser, context, args):
    log.debug("Running '{}'" . format('list_services'))
    log.debug("Listing all Service ID...")

    args = parser.parse_args(args)

    obj = None
    try:
        obj = cmd_list(parser, context, args, 'Services/keys')
    except:
        log.exception("Sorry could not get the list of '{}' from the input file!".format('services'))
        exit(1)

    assert obj is not None

    if isinstance(obj, Base):
        print(yaml_dump(obj.data_dump()))
    else:
        print(yaml_dump(obj))

    log.debug("Done")
    exit(0)

def main():
    handler = ArgumentHandler(use_subcommand_help=True, enable_autocompletion=True, description="Hilbert - server tool")

    # add_argument, set_logging_level, set_subcommands,
#    handler.add_argument('-q', '--quiet', help='decrease verbosity', action='store_true')
#    handler.add_argument('-v', '--verbose', help='increase verbosity', action='store_true')

#    handler.set_logging_argument('-l', '--log_level', default_level=logging.INFO)

    # no arguments: 'store_const', 'store_true' or 'store_false'
    handler.add_argument('-p', '--pedantic', required=False, action='store_true',
                         help="turn on pedantic mode")

    # 2 input sources: .YAML or .PICKLE
    handler.add_argument('-if', '--inputfile', required=False, 
                         help="specify input .YAML file (default: 'Hilbert.yml')")
    handler.add_argument('-id', '--inputdump', required=False,
                         help="specify input dump file")
                         
    _argv = sys.argv[1:]

    # NOTE: show help by if not arguments given
    if len(_argv) == 0:
        log.debug("No command arguments given => Showing usage help!")
        _argv = ['-h']

    handler.run(_argv)


main()
