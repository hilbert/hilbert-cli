# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals  # NOQA

from ..hilbert_cli_config import load_yaml, _load, _parse, INPUT_DIRNAME #, _pprint

import pytest                        # NOQA
import os                            # NOQA


FIXTURE_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
        'data',
            ))


import dill as pickle # 3-clause BSD 

class TestValidate:
    def test_1(self, capsys):
        global INPUT_DIRNAME

        g = os.path.join(FIXTURE_DIR, 'Hilbert.yml')
        f = os.path.join(FIXTURE_DIR, 'Hilbert.yml.data.pickle')

        print(g)
        print(f)

        assert os.path.exists(g)
        assert os.path.exists(f)

        yml = _load(g)
        assert yml is not None

        INPUT_DIRNAME = FIXTURE_DIR

        cwd = os.getcwd()
        try:
            os.chdir(INPUT_DIRNAME)
            cfg = _parse(yml)
        finally:
            os.chdir(cwd)

        assert cfg is not None       
#        _pprint(cfg)
        
        with open(f, 'rb') as p:
            # Pickle the 'data' dictionary using the highest protocol available.
            d = pickle.load(p)
#            _pprint(d)
            assert d == cfg
