#!/usr/bin/env python2

# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

from hilbert_cli_config import *
from helpers import *

from arghandler import *               # NOQA 
import argparse                        # NOQA

import logging
# log = logging.getLogger(__name__)

def _version():
    import platform
    import dill
    import ruamel.yaml as yaml
    print("## Python Version: '{}'".format(platform.python_version()))
    print("## ruamel.yaml Version: '{}'".format(yaml.__version__))
    print("## dill Version: '{}'".format(dill.__version__))
    # arghandler version? dill version? etc?

def _load(f):
    print("## YAML Validation: ")
    return load_yaml_file(f)  # TODO: check that this is a dictionary!


@subcmd('version', help='Print version info')
def cmd_version(parser, context, args):
    _version()


@subcmd('cfg_verify', help='Check correctness of a given general Hilbert configuration (YAML) file as far as possible...')
def cmd_verify(parser, context, args):
    global PEDANTIC
    global INPUT_DIRNAME
    global OUTPUT_DIRNAME

    ctx = vars(context)

    if 'pedantic' in ctx:
        PEDANTIC = ctx['pedantic']


    args = vars(parser.parse_args(args))
#    vars(args)
        
    fn = ctx['inputfile']
    assert fn is not None

    f = URI(None)
    if f.validate(fn):
        fn = f.get_data()
        print("## Input file: '{}'".format(fn))
    else:
        print("ERROR: wrong file specification: '{}'" . format(fn))
        exit(1)

    INPUT_DIRNAME = os.path.abspath(os.path.dirname(fn))

    print("## Loading '{}'..." . format(fn))
    try:
        yml = _load(fn)
        print("## Input file is a valid YAML!")
    except:
        print("ERROR: wrong input file: '{}'!" . format(fn))
        raise

    os.chdir(INPUT_DIRNAME)
    print("## Deep Configuration Validation/Parsing: ")
    cfg = parse(yml)

    if cfg is None:
        print("ERROR: semantically wrong input!")
        exit(1)
        
    print("## Input file is a good Hilbert configuration!")

#    return cfg


@subcmd('cfg_dump', help='Load input .YAML or .Pickle file and dump it')
def cmd_dump(parser, context, args):
    global PEDANTIC
    global INPUT_DIRNAME
    global OUTPUT_DIRNAME

    parser.add_argument('-O', '--outputdir', required=False, default=argparse.SUPPRESS,
            help="specify output directory (default: alongside with the output dump file)")
            
    parser.add_argument('-od', '--outputdump', required=True, default=argparse.SUPPRESS,
            help="specify output file (default: same as the input file with '.pickle' suffix)")

    ctx = vars(context)

    if 'pedantic' in ctx:
        PEDANTIC = ctx['pedantic']

    args = vars(parser.parse_args(args))
        
    fn = None
    df = None
    
    f = URI(None)

    if 'inputfile' in ctx:
        fn = ctx['inputfile']
#        assert fn is not None
        
    if 'inputdump' in ctx:
        df = ctx['inputdump']
#        assert df is not None
        
    if fn is not None:        
        if not f.validate(fn):
            print("ERROR: wrong file specification: '{}'" . format(fn))
            exit(1)            
        print("## Input file: '{}'".format(fn))
        
    if df is not None:        
        if not f.validate(df):
            print("ERROR: wrong dump file specification: '{}'" . format(df))
            exit(1)
        print("## Input dump file: '{}'".format(df))
        

    if (fn is None) and (df is None):
        print("ERROR: input file/dump specification is missing!")
        exit(1)
        
    if (fn is not None) and (df is not None):
        print("ERROR: input file specification clashes with the input dump specification: specify a single input source!")
        exit(1)
        
        
    if fn is not None:
        INPUT_DIRNAME = os.path.abspath(os.path.dirname(fn))
    else:
        assert df is not None
        INPUT_DIRNAME = os.path.abspath(os.path.dirname(df))


    out = None
    
    if 'outputdir' in args:
        out = args['outputdir']
        
        assert out is not None

        if not f.validate(out):
            print("ERROR: wrong output directory specification: '{}'" . format(out))
            exit(1)
            
#        out = f.get_data()
        print("## Output dir: '{}'".format(out))

        OUTPUT_DIRNAME = os.path.abspath(out)
    else:
        OUTPUT_DIRNAME = INPUT_DIRNAME        
        
    od = None

    if 'outputdump' in args:
        od = args['outputdump']
        assert od is not None
    elif fn is not None:
        od = os.path.splitext(os.path.basename(fn))[0] + '.pickle'
        OUTPUT_DIRNAME = INPUT_DIRNAME
    else:
        assert df is not None
        od = os.path.splitext(os.path.basename(df))[0] + '.pickle'
        OUTPUT_DIRNAME = INPUT_DIRNAME        

        
    f = URI(None)
    if not f.validate(od):
        if not PEDANTIC:
            print("## WARNING: Output dump file: '{}' already exists!".format(od))
        else:
            print("## ERROR: Output dump file: '{}' already exists!".format(od))
            exit(1)

    cfg = None
    if fn is not None:
        print("## Loading '{}'..." . format(fn))
        try:
            yml = _load(fn)
            print("## Input file is a valid YAML!")

            os.chdir(INPUT_DIRNAME)
            print("## Data Validation/Parsing: ")
            cfg = parse(yml)
            
        except:
            print("ERROR: wrong input file: '{}'!" . format(fn))
            raise
    else:
        print("## Loading dump '{}'..." . format(df))
        try:
            cfg = pickle_load(df)
            print("## Input dump file is valid!")
        except:
            print("ERROR: wrong input dump file: '{}'!" . format(df))
            raise
        

    if cfg is None:
        print("ERROR: semantically wrong input!")
        exit(1)

    print("## Input is OK!")

    print("## Writing the configuration into '{}'..." . format(od))
    pickle_dump(od, cfg)
    print("## Pickled configuration is now in '{}'!" . format(od))


#    return cfg



def main():
    handler = ArgumentHandler(use_subcommand_help=True, enable_autocompletion=True, description="Validate/Parse Hilbert Configuration")

    # add_argument, set_logging_level, set_subcommands,
    handler.add_argument('-q', '--quiet', help='decrease verbosity', action='store_true')
    handler.add_argument('-v', '--verbose', help='increase verbosity', action='store_true')

#    handler.set_logging_argument('-l', '--log_level', default_level=logging.INFO)

    # no arguments: 'store_const', 'store_true' or 'store_false'
    handler.add_argument('-p', '--pedantic', required=False, action='store_true',
                         help="turn on pedantic mode")

    handler.add_argument('-if', '--inputfile', required=False, default='Hilbert.yml',
                         help="specify input file (default: 'Hilbert.yml')")

    handler.add_argument('-id', '--inputdump', required=False,
                         help="specify input dump file")
                         
    _argv = sys.argv
    _argv = _argv[1:]

    if len(_argv) == 0:
        _argv = ['-h']

    handler.run(_argv)

if __name__ == "__main__":
    main()

    