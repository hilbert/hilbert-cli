# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals  # NOQA

import sys
from os import path

DIR=path.dirname( path.dirname( path.abspath(__file__) ) )
sys.path.append( DIR )


from hilbert_cli_config import *
from helpers import *

import pytest                        # NOQA
import os                            # NOQA


FIXTURE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
        'data',
            ))

class TestValidate:
    def test_1(self, capsys):
        global INPUT_DIRNAME

        g = os.path.join(FIXTURE_DIR, 'Hilbert.yml')
        f = os.path.join(FIXTURE_DIR, 'Hilbert.yml.data.pickle')

        print(g)
        print(f)

        assert os.path.exists(g)
        assert os.path.exists(f)

        yml = load_yaml_file(g)
        assert yml is not None

        INPUT_DIRNAME = FIXTURE_DIR

        cwd = os.getcwd()
        try:
            os.chdir(INPUT_DIRNAME)
            cfg = parse_hilbert(yml)
        finally:
            os.chdir(cwd)
        
        assert cfg is not None
        
        d = pickle_load(f)
        
        assert d is not None

        assert type(d) == type(cfg)
        
        pprint(cfg)
        pprint(d)

        assert d == cfg
