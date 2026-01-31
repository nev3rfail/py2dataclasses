# Port of dataclasses tests to Python 2.7
from __future__ import print_function, absolute_import
import os
import sys
import unittest
from dataclasses import *
import dataclasses
#from dataclasses import field
#import src.py2dataclasses
#from src import py2dataclasses
import six

#path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
#sys.path.insert(0, path)

#from dataclasses import *
from functools import wraps
import inspect
try:
    from collections import MutableMapping
except:
    # python 2 hack
    import collections
    from collections.abc import MutableMapping
    object.__setattr__(collections, "MutableMapping", MutableMapping)


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



def choose_2_or_3(for_2, for_3):
    if six.PY2:
        return for_2
    elif six.PY3:
        return for_3

#aa = field()
# import typing
# if typing.TYPE_CHECKING:
#     a = field()
#     #import field
#     # from py2dataclasses import fields, field, Field, dataclass, is_dataclass, replace, make_dataclass, asdict, \
#     #     astuple, FrozenInstanceError, MISSING, InitVar, KW_ONLY
#     #import py2dataclasses.dataclasses as dataclasses

from typing import ClassVar
# path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
# sys.path.append(path)
# from dataclasses import fields, field, Field, dataclass, is_dataclass, replace, make_dataclass, asdict, \
#     astuple, FrozenInstanceError, MISSING, InitVar, KW_ONLY, dataclass
# import dataclasses

try:
    import abc.ABC as ABC
except ImportError:
    from _py2dataclasses import abc_utils as __abc_utils
    #import __abc_utils.ABC as ABC
    ABC = __abc_utils.ABC
#sys.modules["dataclasses"] = dataclasses
#import unittest2 as unittest
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
import typing
import weakref
# Just any custom exception we can catch.
if not getattr(unittest.TestCase, "assertRaisesRegexp", None):
    unittest.TestCase.assertRaisesRegexp = unittest.TestCase.assertRaisesRegex
#assertRaisesRegexp = getattr(unittest.TestCase, "assertRaisesRegex", getattr(unittest.TestCase, "assertRaisesRegexp", None))
class CustomError(Exception): pass
