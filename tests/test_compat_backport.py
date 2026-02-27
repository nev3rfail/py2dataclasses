"""Run _fixtures_py314 (CPython 3.14 stdlib) tests through py2dataclasses.

Patches the fixture module to use our library instead of stdlib dataclasses.
"""
import sys
import os
import unittest

_project_root = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

import src.dataclasses as py2dataclasses


def field_adapter(*args, **kwargs):
    kwargs.setdefault('mode', 0)
    return py2dataclasses.field(*args, **kwargs)


def _dataclass_adapter(cls, *args, **kwargs):
    return py2dataclasses.dataclass(cls, *args, **kwargs)


def dataclass_adapter(cls=None, /, *, init=True, repr=True, eq=True, order=False,
                      unsafe_hash=False, frozen=False, match_args=True,
                      kw_only=False, slots=False, weakref_slot=False):
    kwargs = dict(init=init, repr=repr, eq=eq, order=order,
                  unsafe_hash=unsafe_hash, frozen=frozen, match_args=match_args,
                  kw_only=kw_only, slots=slots, weakref_slot=weakref_slot)
    if cls is None:
        def wrapper(c):
            return _dataclass_adapter(c, **kwargs)
        return wrapper
    else:
        return _dataclass_adapter(cls, **kwargs)


def patch_test(target_module):
    field_list = ('fields', 'field', 'Field', 'dataclass', 'is_dataclass', 'replace',
                  'make_dataclass', 'asdict', 'astuple', 'FrozenInstanceError', 'MISSING',
                  '_oneshot', 'InitVar', 'KW_ONLY')
    patch_map = {"field": field_adapter, "dataclass": dataclass_adapter}
    for one in field_list:
        if one in patch_map:
            target_module.__setattr__(one, patch_map[one])
        else:
            target_module.__setattr__(one, getattr(py2dataclasses, one))
    target_module.__setattr__('dataclasses', py2dataclasses)


def load_tests(loader, tests, pattern):
    mod = __import__("_fixtures_py314")
    patch_test(mod)
    return loader.loadTestsFromModule(mod)


if __name__ == '__main__':
    unittest.main()
