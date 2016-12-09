# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals  # NOQA

import sys
from os import path
DIR=path.dirname( path.dirname( path.abspath(__file__) ) )
sys.path.append(DIR)
sys.path.append(path.join(DIR, 'config'))

from helpers import *
from hilbert_cli_config import *
from subcmdparser import *

#from config.hilbert_cli_config import *
#from config.helpers import *
#from config.subcmdparser import *


# sys.path.append( DIR )

#from hilbert_cli_config import *
#from helpers import *

import pytest                        # NOQA
import os                            # NOQA


FIXTURE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
        'data',
            ))

def hilbert_validation(input_yaml_file, data_file):
    global INPUT_DIRNAME

    input_file = os.path.join(FIXTURE_DIR, input_yaml_file)
    data_file = os.path.join(FIXTURE_DIR, data_file)

    assert os.path.exists(input_file)
    assert os.path.exists(data_file)

    # Load Hilbert configuration in YAML format
    yml = load_yaml_file(input_file)
    assert yml is not None

    # Load previously verified data
    d = pickle_load(data_file)
    assert d is not None
    assert isinstance(d, dict)

    cwd = os.getcwd()
    try:
        INPUT_DIRNAME = FIXTURE_DIR
        os.chdir(INPUT_DIRNAME)
        cfg = parse_hilbert(yml)
    finally:
        os.chdir(cwd)

    assert cfg is not None
    assert isinstance(cfg, Hilbert)

    data = cfg.data_dump()
    assert isinstance(data, dict)

    #        print(cfg)
    #        print(yaml_dump(data))
    #        print(yaml_dump(d))

    # NOTE: Main check:
    assert data == d  # Compare dictionaries with simple data!


class TestValidate:
    def test_minimal_sample(self, capsys):
        hilbert_validation('miniHilbert.yml', 'miniHilbert.yml.data.pickle')

    def test_sample(self, capsys):
        hilbert_validation('Hilbert.yml', 'Hilbert.yml.data.pickle')

    def test_single(self, capsys):
        hilbert_validation('singleHostHilbert.yml', 'singleHostHilbert.yml.data.pickle')
