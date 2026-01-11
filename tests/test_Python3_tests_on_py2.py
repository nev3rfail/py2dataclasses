import sys
import os
import six
path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "dataclasses"))
sys.path.insert(0, path)

import src.dataclasses as py2dataclasses
# from src.dataclasses import fields, field, Field, dataclass, is_dataclass, replace, make_dataclass, asdict, \
#     astuple, FrozenInstanceError, MISSING, _oneshot
from collections import OrderedDict
import unittest

def field_adapter(*args, **kwargs):
    f = py2dataclasses.field(*args, **kwargs)
    #f.type = _typ
    return f

def collect_annotations(cls):
    items = {}
    i = 0
    for name, value in cls.__dict__.items():
        if isinstance(value, py2dataclasses.Field):
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

def _dataclass_adapter(cls, *args, **kwargs):
    #ann = collect_annotations(cls)
    #if ann:
    #    annotate(ann)(cls)
    f = py2dataclasses.dataclass(cls, *args, **kwargs)
    #f.type = _typ
    return f


def dataclass_adapter(cls=None, *args, **kwargs):
    if cls is None:
        return _dataclass_adapter
    else:
        return _dataclass_adapter(cls)





def patch_test(target_module):
    field_list = ('fields', 'field', 'Field', 'dataclass', 'is_dataclass', 'replace', 'make_dataclass', 'asdict', 'astuple', 'FrozenInstanceError', 'MISSING', '_oneshot')
    patch_map = {"field": field_adapter, "dataclass": dataclass_adapter}
    for one in field_list:

        if one in patch_map:
            target_module.__setattr__(one, patch_map[one])
        else:
            target_module.__setattr__(one, getattr(py2dataclasses, one))


def load_tests(loader, tests, pattern):
    # Import the real test module
    mod = __import__("test_Dataclasses_py314")
    patch_test(mod)
    suite = loader.loadTestsFromModule(mod)
    return suite

if __name__ == '__main__':
    loader = unittest.TestLoader()
    root_suite = loader.loadTestsFromName("test_Dataclasses_py314")
    patch_test(sys.modules["test_Dataclasses_py314"])
    runner = unittest.TextTestRunner(verbosity=2)