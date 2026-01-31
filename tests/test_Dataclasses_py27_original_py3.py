import sys
import os
from collections import OrderedDict
import unittest
#import pytest
#path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
#sys.path.insert(0, path)
#print(sys.path)
try:
    from dataclasses import fields, field, Field, dataclass, is_dataclass, replace, make_dataclass, asdict, \
        astuple, FrozenInstanceError, MISSING
except:
    print("wtf")
    pass
def field_adapter(_typ, *args, **kwargs):
    f = field(*args, **kwargs)
    f.type = _typ
    return f

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
            #i = value.order
        # elif is_descriptor(value):
        #     # TODO: warning here, we shouldn't allow implicit typing
        #     t = type(value)
        #     items.append((i, name, t))
        # i += 1
        # elif not name.startswith("__"):
        #     # TODO: warning here, we shouldn't allow implicit typing
        #     t = type(value)
        #     items.append((i, name, t))
        # i += 1



    #items.sort(key=lambda x: x[0])  # sort by descriptor order

    #ret = OrderedDict((name, t) for _, name, t in items)
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
    f = dataclass(cls, *args, **kwargs)
    #f.type = _typ
    return f


def dataclass_adapter(cls=None, *args, **kwargs):
    if cls is None:
        return _dataclass_adapter
    else:
        return _dataclass_adapter(cls)





def patch_test(mod):
    object.__setattr__(mod, "_real_field", mod.field)
    object.__setattr__(mod, "field", field_adapter)

    object.__setattr__(mod, "_real_dataclass", mod.dataclass)
    object.__setattr__(mod, "dataclass", dataclass_adapter)

    pass

def load_tests(loader, tests, pattern):
    # Import the real test module
    mod = __import__("tests.test_Dataclasses_py27")
    mod = mod.test_Dataclasses_py27
    patch_test(mod)

    # Now load the tests normally
    suite = loader.loadTestsFromName("tests.test_Dataclasses_py27")
    return suite

if __name__ == '__main__':
    loader = unittest.TestLoader()
    root_suite = loader.discover("tests.test_Dataclasses_py27", top_level_dir=os.getcwd()) #loader.loadTestsFromName("tests.test_Dataclasses_py27")
    patch_test(sys.modules["tests.test_Dataclasses_py27"].common)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(root_suite)
#test_running()
#return pew