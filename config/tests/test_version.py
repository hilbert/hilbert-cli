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

from semantic_version import Version  # supports partial versions

class TestVersions:
    def test_1(self):
        v = '0.0'
        assert Version(v, partial=True) == \
               SemanticVersion.parse(load("'{}'" . format(v)), partial=True).get_data()

        v = '0.1'
        assert Version(v, partial=True) == \
               SemanticVersion.parse(load("'{}'" . format(v)), partial=True).get_data()

        v = '1.2'
        assert Version(v, partial=True) == \
               SemanticVersion.parse(load("'{}'" . format(v)), partial=True).get_data()

    def test_2(self):
        v = '0.0.1'
        assert Version(v) == SemanticVersion.parse(load("'{}'" . format(v))).get_data()

        v = '0.1.2'
        assert Version(v) == SemanticVersion.parse(load("'{}'" . format(v))).get_data()

        v = '1.2.3'
        assert Version(v) == SemanticVersion.parse(load("'{}'" . format(v))).get_data()
