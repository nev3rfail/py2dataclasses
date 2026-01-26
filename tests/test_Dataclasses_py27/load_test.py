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
# Try to expose typing.get_type_hints for tests that expect it; if unavailable
# in Python 2.7, define a placeholder that will cause those tests to fail as
# intended per project policy.
try:
    from typing import get_type_hints  # type: ignore
except Exception:
    def get_type_hints(obj):  # type: ignore
        # Trigger failure in tests that rely on typing support in py2
        raise ImportError("typing.get_type_hints is not available on Python 2.7")
import pickle
import copy
import types
import weakref
# Just any custom exception we can catch.
class CustomError(Exception): pass
class ABC(object):
    __metaclass__ = abc.ABCMeta