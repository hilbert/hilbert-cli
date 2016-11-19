# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals  # NOQA

from ..hilbert_cli_config import load_yaml
# from ..helpers import load_yaml

import pytest                        # NOQA

def load(s):
    return load_yaml(s)

class TestLoad:
    def test_1(self, capsys):
        out, err = capsys.readouterr()        
        load('{a, b, a}')       
        out, err = capsys.readouterr()
        
#        with capsys.disabled():
        assert err == ''
        assert out == """\
WARNING: Key re-definition within some mapping: 
K[line: 1, column: 2]: Previous Value: 
 a: None
 ↑
---
K[line: 1, column: 8]: New Value: 
       a: None
       ↑
---
===
"""



    def test_2(self, capsys):
        out, err = capsys.readouterr()        
        load("""{ ? a, ? b, ? a }""")
        out, err = capsys.readouterr()
        
        assert err == ''
        assert out == """\
WARNING: Key re-definition within some mapping: 
K[line: 1, column: 5]: Previous Value: 
    a: None
    ↑
---
K[line: 1, column: 15]: New Value: 
              a: None
              ↑
---
===
"""
   
        


        
        
