# -*- coding: utf-8 -*-
# encoding: utf-8
# coding: utf-8

from __future__ import absolute_import, print_function, unicode_literals

# from .hilbert_cli_config import load_yaml # Hilbert # VerboseRoundTripLoader, 

###############################################################
# import pickle
# import cPickle as pickle

def pickle_dump(fn, d):
    import dill as pickle  # NOTE: 3-clause BSD
    with open(fn, 'wb') as p:
        # NOTE: Pickle the 'data' dictionary using the highest protocol available?
        # pickle.HIGHEST_PROTOCOL = 4 added in Python 3.4
        pickle.dump(d, p, 2) # 2nd PROTOCOL was introduced in Python 2.3.
        
def pickle_load(fn):
    import dill as pickle  # NOTE: 3-clause BSD
    with open(fn, 'rb') as p:
        d = pickle.load(p)
    return d

###############################################################

def yaml_dump(d, stream=None):
    import ruamel.yaml as yaml
    print(yaml.round_trip_dump(d, stream=stream))
