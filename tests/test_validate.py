# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals  # NOQA

import sys
from os import path
from ruamel.yaml.compat import PY2, PY3, text_type, string_types, ordereddict

DIR=path.dirname( path.dirname( path.abspath(__file__) ) )
sys.path.append(DIR)
sys.path.append(path.join(DIR, 'hilbert_config'))

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
import logging
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)  # TODO: FIXME: no log output!?

FIXTURE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
        'data',
            ))

def hilbert_invalidation(capsys, bad_input_yaml_file, test_output, test_err):
    input_file = os.path.join(FIXTURE_DIR, bad_input_yaml_file)
    assert os.path.exists(input_file)

    yml = load_yaml_file(input_file)
    assert yml is not None

    out, err = capsys.readouterr()
    try:
        cwd = os.getcwd()
        old = set_INPUT_DIRNAME(FIXTURE_DIR)
        try:
            os.chdir(get_INPUT_DIRNAME())
            cfg = parse_hilbert(yml)
        finally:
            set_INPUT_DIRNAME(old)
            os.chdir(cwd)
        # must throw an exception!
        assert False
    except:
        assert True
        pass
    out, err = capsys.readouterr()

    assert out == test_output
    assert err == test_err


def hilbert_validation(input_yaml_file, data_file):

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
    old = set_INPUT_DIRNAME(FIXTURE_DIR)
    try:
        os.chdir(get_INPUT_DIRNAME())
        cfg = parse_hilbert(yml)
    finally:
        set_INPUT_DIRNAME(old)
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

    def test_non_unique_app_service_ids(self, capsys):
        test_output = None

        if PY2:
            test_err = ''

            test_output = """\
K[line: 4, column: 3]: Service key: duplicating_id
  duplicating_id: ordereddict([('type', 'compose'), ('ref', 'hb_test')])
  ↑
---
K[line: 7, column: 3]: Application key: duplicating_id
  duplicating_id: ordereddict([('type', 'compose'), ('ref', 'hb_test'), ('file', 'docker-compose.yml'), ('name', 'HB-Test'), ('description', 'Random HB testing'), ('compatible_stations', ordereddict([]))])
  ↑
---
"""
        elif PY3:
            test_err = ''
# """'duplicating_id' is both a ServiceID and an ApplicationID:"""

            test_output = """\
K[line: 4, column: 3]: Service key: duplicating_id
  duplicating_id: CommentedMap([('type', 'compose'), ('ref', 'hb_test')])
  ↑
---
K[line: 7, column: 3]: Application key: duplicating_id
  duplicating_id: CommentedMap([('type', 'compose'), ('ref', 'hb_test'), ('file', 'docker-compose.yml'), ('name', 'HB-Test'), ('description', 'Random HB testing'), ('compatible_stations', CommentedMap())])
  ↑
---
"""
        hilbert_invalidation(capsys, 'non_unique_app_service_ids_Hilbert.yml', test_output, test_err)
