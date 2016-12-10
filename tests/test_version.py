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
sys.path.append(path.join(DIR, 'config'))

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

    return v == validator_data


class TestVersions:
    def test_good(self):
        v = '0.0.1'
        assert _helper(v)

        v = '0.1.2'
        assert _helper(v)

        v = '1.2.3'
        assert _helper(v)

    def test_good_partial(self):
        v = '0.0'
        assert _helper(v, partial=True)

        v = '0.1'
        assert _helper(v, partial=True)

        v = '1.2'
        assert _helper(v, partial=True)

# TODO: add failure tests: e.g. wrong version + with exceptions...