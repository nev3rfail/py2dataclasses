import functools
import types
import unittest
#import tests.test_Dataclasses_py314
import os,sys
path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.insert(0, path)

import py2dataclasses as dataclasses
import _py2dataclasses as _py2dataclasses
#from . import dataclasses
def field_adapter(*args, **kwargs):
    f = dataclasses._real_field(*args, **kwargs)
    #if _typ is not dataclasses.MISSING:
    #    f.type = _typ
    return f
def _dataclass_adapter(cls, *args, **kwargs):
    #ann = collect_annotations(cls)
    #if ann:
    #    annotate(ann)(cls)
    f = dataclasses._real_dataclass(cls, *args, **kwargs)
    #f.type = _typ
    return f

def dataclass_adapter(cls=None, *args, **kwargs):
    if cls is None:
        return functools.partial(_dataclass_adapter, *args, **kwargs)
    else:
        return _dataclass_adapter(cls, *args, **kwargs)



def patch_test(target_module):
    ##sys.modules["dataclasses"] = py2dataclasses
    field_list = ('fields', 'field', 'Field',
                  'dataclass', 'is_dataclass',
                  'replace', 'make_dataclass',
                  'asdict', 'astuple',
                  'FrozenInstanceError',
                  'MISSING', '_oneshot', 'KW_ONLY')
    patch_map = {"field": field_adapter, "dataclass": dataclass_adapter}
    for one in field_list:

        if one in patch_map:
            target_module.__setattr__("_real_"+one, getattr(target_module, one))
            target_module.__setattr__(one, patch_map[one])
        else:
            target_module.__setattr__(one, getattr(dataclasses, one))
    #setattr(target_module, "__was_patched", True)


##sys.modules["dataclasses"] = py2dataclasses
#patch_test(sys.modules["tests.test_Dataclasses_py314"].common)
import sys
import os
import six


##print(sys.path)

# from src.dataclasses import fields, field, Field, dataclass, is_dataclass, replace, make_dataclass, asdict, \
#     astuple, FrozenInstanceError, MISSING, _oneshot
from collections import OrderedDict



def collect_annotations(cls):
    items = {}
    i = 0
    for name, value in cls.__dict__.items():
        if isinstance(value, dataclasses.Field):
            t = value.type
            if t is None:
                raise TypeError(
                    '{0!r} is a field but has no type annotation'.format(name)
                )
            value.__set_name__(cls, name)
            items[name] =  t
    return items

def annotate(__annotations__, **kwargs):
    """Python 3 compatible function annotation for Python 2."""
    if __annotations__ and not kwargs:
        kwargs = __annotations__
    if not kwargs:
        raise ValueError('annotations must be provided as keyword arguments')
    def dec(f):
        if hasattr(f, '__annotations__'):
            for k, v in kwargs.items():
                f.__annotations__[k] = v
        else:
            f.__annotations__ = OrderedDict(kwargs)
        return f
    return dec

# def _dataclass_adapter(cls, *args, **kwargs):
#     #ann = collect_annotations(cls)
#     #if ann:
#     #    annotate(ann)(cls)
#     f = _py2dataclasses.dataclass(cls, *args, **kwargs)
#     #f.type = _typ
#     return f

def load_tests(loader, tests, pattern):
    # Import the real test module
    _old = sys.modules["dataclasses"]
    sys.modules["dataclasses"] = dataclasses
    patch_test(sys.modules["dataclasses"])
    from .test_Dataclasses_py314 import common
    #sys.modules["dataclasses"] = _old
    suite = loader.discover("tests.test_Dataclasses_py314", top_level_dir=os.getcwd())
    patch_test(sys.modules["tests.test_Dataclasses_py314"].common)
    #mod = mod.test_Dataclasses_py314
    #patch_test(sys.modules["tests.test_Dataclasses_py314"].common)
    #suite = loader.loadTestsFromName("tests.test_Dataclasses_py314")
    return suite


#print("AAA", os.getcwd(), __name__, "\n", f"s{ __spec__.name}s", file=open("test1.log", "w"))
if __name__ == '__main__':
    loader = unittest.TestLoader()
    #print("AAA", os.getcwd(), file=sys.stderr)
    root_suite = loader.discover("tests.test_Dataclasses_py314", top_level_dir=os.getcwd())
    #print(root_suite, file=open("test_ss.log", "w"))
    patch_test(sys.modules["tests.test_Dataclasses_py314"].common)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(root_suite)