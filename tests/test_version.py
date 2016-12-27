# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals  # NOQA

import sys
from os import path
import logging
logging.basicConfig(level=logging.WARNING, stream=sys.stderr)  # TODO: FIXME: no log output!?

DIR=path.dirname( path.dirname( path.abspath(__file__) ) )
sys.path.append(DIR)
sys.path.append(path.join(DIR, 'hilbert_config'))

# from helpers import *
from hilbert_cli_config import SemanticVersionValidator, load_yaml
# from subcmdparser import *

import pytest                        # NOQA

# NOTE: supports partial versions!
import semantic_version              # NOQA


# TODO: FIXME: set globally format version for SemanticVersionValidator!

def _helper(s, partial=False):
    v = None
    try:
        v = semantic_version.Version(s, partial=partial)
    except:
        pass

    assert v is not None
    assert isinstance(v, semantic_version.Version)

    yaml_data = load_yaml("'{}'".format(s))
    assert yaml_data is not None

    # NOTE: Validator parsing
    validator = SemanticVersionValidator.parse(yaml_data, parent=None, partial=partial, parsed_result_is_data=False)

    assert validator is not None
    assert isinstance(validator, SemanticVersionValidator)
    validator_data = validator.get_data()
    assert validator_data is not None
    assert isinstance(validator_data, semantic_version.Version)

    assert v == validator_data
    return v


class TestVersions:
    def test_good(self):
        v001 = _helper('0.0.1')

        v012 = _helper('0.1.2')
        assert v012 > v001

        v123 = _helper('1.2.3')
        assert v123 > v012
        assert v123 > v001

    def test_good_partial(self):
        v00 = _helper('0.0', partial=True)   # 0.0.0?

        assert _helper('0.0.1') >= v00

        v01 = _helper('0.1', partial=True)
        assert v01 > v00
        assert _helper('0.1.2') >= v01

        v12 = _helper('1.2', partial=True)
        assert v12 > v01
        assert v12 > v00
        assert _helper('1.2.3') >= v12

# TODO: add failure tests: e.g. wrong version + with exceptions...