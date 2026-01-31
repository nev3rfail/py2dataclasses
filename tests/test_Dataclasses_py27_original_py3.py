import functools
import sys
import os
from collections import OrderedDict
import unittest
import dataclasses

def field_adapter(_typ=dataclasses.MISSING, *args, **kwargs):
    f = dataclasses._real_field(*args, **kwargs)
    if _typ is not MISSING:
        f.type = _typ
    return f
def _dataclass_adapter(cls, *args, **kwargs):
    ann = collect_annotations(cls)
    if ann:
        annotate(ann)(cls)
    f = dataclasses._real_dataclass(cls, *args, **kwargs)
    #f.type = _typ
    return f

def dataclass_adapter(cls=None, *args, **kwargs):
    if cls is None:
        return functools.partial(_dataclass_adapter, *args, **kwargs)
    else:
        return _dataclass_adapter(cls, *args, **kwargs)

def patch_test(mod):
    object.__setattr__(mod, "_real_field", mod.field)
    object.__setattr__(mod, "field", field_adapter)

    object.__setattr__(mod, "_real_dataclass", mod.dataclass)
    object.__setattr__(mod, "dataclass", dataclass_adapter)

    pass
patch_test(sys.modules["dataclasses"])
try:
    from dataclasses import fields, field, Field, dataclass, is_dataclass, replace, make_dataclass, asdict, \
        astuple, FrozenInstanceError, MISSING
except:
    raise

def collect_annotations(cls):
    items = {}
    i = 0
    for name, value in cls.__dict__.items():
        if isinstance(value, Field):
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
    ann = collect_annotations(cls)
    if ann:
        annotate(ann)(cls)
    f = dataclasses._real_dataclass(cls, *args, **kwargs)
    #f.type = _typ
    return f




def load_tests(loader, tests, pattern):
    # Import the real test module
    suite = loader.discover("tests.test_Dataclasses_py27", top_level_dir=os.getcwd()) #loader.loadTestsFromName("tests.test_Dataclasses_py27")
    #patch_test(sys.modules["dataclasses"].common)

    # Now load the tests normally
    #suite = loader.loadTestsFromName("tests.test_Dataclasses_py27")
    return suite

if __name__ == '__main__':
    loader = unittest.TestLoader()
    suite = loader.discover("tests.test_Dataclasses_py27", top_level_dir=os.getcwd()) #loader.loadTestsFromName("tests.test_Dataclasses_py27")
    #patch_test(sys.modules["tests.test_Dataclasses_py27"].common)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
#test_running()
#return pew