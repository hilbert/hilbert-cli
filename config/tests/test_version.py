# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals  # NOQA

from ..hilbert_cli_config import SemanticVersion
from ..hilbert_cli_config import load_yaml
# helpers

import pytest                        # NOQA


def load(s):
    return load_yaml(s)

from semantic_version import Version # supports partial versions

class TestVersions:
    def test_1(self):
        v = '0.0'
        assert Version.parse(v, partial=True, coerce=True) == SemanticVersion.parse(load("'{}'" . format(v)))

        v = '0.1'
        assert Version.parse(v, partial=True, coerce=True) == SemanticVersion.parse(load("'{}'" . format(v)))

        v = '1.2'
        assert Version.parse(v, partial=True, coerce=True) == SemanticVersion.parse(load("'{}'" . format(v)))

        
    def test_2(self):
        v = '0.0.1'
        assert Version.parse(v, partial=True, coerce=True) == SemanticVersion.parse(load("'{}'" . format(v)))

        v = '0.1.2'
        assert Version.parse(v, partial=True, coerce=True) == SemanticVersion.parse(load("'{}'" . format(v)))

        v = '1.2.3'
        assert Version.parse(v, partial=True, coerce=True) == SemanticVersion.parse(load("'{}'" . format(v)))
        
        