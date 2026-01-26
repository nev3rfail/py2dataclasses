# Port of dataclasses tests to Python 2.7
from __future__ import print_function, absolute_import
import os
import sys
path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..", "src"))
sys.path.insert(0, path)

try:
    from collections import MutableMapping
except:
    # python 2 hack
    import collections
    from collections.abc import MutableMapping
    object.__setattr__(collections, "MutableMapping", MutableMapping)

import abc
import funcsigs

from collections import OrderedDict
from contextlib import contextmanager
import sys

@contextmanager
def expose_to_test(*classes):
    saved = []
    try:
        for cls in classes:
            mod = sys.modules[cls.__module__]
            saved.append((mod, cls.__name__, getattr(mod, cls.__name__, None)))
            setattr(mod, cls.__name__, cls)
        yield
    finally:
        for mod, name, orig in saved:
            if orig is None:
                delattr(mod, name)
            else:
                setattr(mod, name, orig)






path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..",".."))
sys.path.append(path)
from py2dataclasses.dataclasses import fields, field, Field, dataclass, is_dataclass, replace, make_dataclass, asdict, \
    astuple, FrozenInstanceError, MISSING, InitVar
import py2dataclasses.dataclasses as dataclasses
sys.modules["dataclasses"] = dataclasses
import unittest2 as unittest
import pickle
import copy
import types
import weakref
# Just any custom exception we can catch.
class CustomError(Exception): pass
class ABC(object):
    __metaclass__ = abc.ABCMeta