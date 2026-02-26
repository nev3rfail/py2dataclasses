"""Run _fixtures_py27_py314 tests against stdlib dataclasses on Python 3.14.

Adapts py2dataclasses field(type) syntax to stdlib field() via monkey-patching.
"""
import sys
import typing
from collections import OrderedDict
import unittest

from dataclasses import fields, field, Field, dataclass, is_dataclass, replace, make_dataclass, asdict, \
    astuple, FrozenInstanceError, MISSING, InitVar
import dataclasses as _stdlib_dataclasses


def _is_type_annotation(obj):
    """Check if obj looks like a type annotation rather than a plain value."""
    return (isinstance(obj, type)
            or hasattr(obj, '__origin__')
            or isinstance(obj, str)
            or isinstance(obj, typing.TypeVar)
            or isinstance(obj, InitVar)
            or (hasattr(typing, '_SpecialForm')
                and isinstance(obj, typing._SpecialForm)))


def field_adapter(_typ=None, *args, **kwargs):
    if args:
        kwargs['default'] = args[0]
    kwargs.pop('mode', None)
    if _typ is not None and not isinstance(_typ, Field):
        if _is_type_annotation(_typ):
            f = field(**kwargs)
            f.type = _typ
        else:
            kwargs.setdefault('default', _typ)
            f = field(**kwargs)
            f.type = type(_typ)
    else:
        f = field(**kwargs)
        if f.type is None and 'default' in kwargs and kwargs['default'] is not None:
            f.type = type(kwargs['default'])
    return f


def _adapter_is_classvar(tp):
    return (tp is typing.ClassVar
            or (hasattr(tp, '__origin__') and tp.__origin__ is typing.ClassVar))


def collect_annotations(cls):
    items = {}
    for name, value in cls.__dict__.items():
        if isinstance(value, Field):
            t = value.type
            if t is None:
                raise TypeError(
                    '{0!r} is a field but has no type annotation'.format(name)
                )
            value.__set_name__(cls, name)
            items[name] = t
    return items


def annotate(__annotations__, **kwargs):
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
    if not cls.__annotations__:
        ann = collect_annotations(cls)
        if ann:
            annotate(ann)(cls)
            for name, tp in ann.items():
                if _adapter_is_classvar(tp):
                    field_obj = cls.__dict__.get(name)
                    if isinstance(field_obj, Field) and field_obj.default is not MISSING:
                        type.__setattr__(cls, name, field_obj.default)
    return dataclass(cls, *args, **kwargs)


def dataclass_adapter(cls=None, init=True, repr=True, eq=True, order=False,
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


def asdict_adapter(obj, dict_factory=OrderedDict):
    return asdict(obj, dict_factory=dict_factory)


def load_tests(loader, tests, pattern):
    mod = __import__("_fixtures_py27_py314")

    object.__setattr__(mod, "_real_field", mod.field)
    object.__setattr__(mod, "field", field_adapter)
    object.__setattr__(mod, "_real_dataclass", mod.dataclass)
    object.__setattr__(mod, "dataclass", dataclass_adapter)
    object.__setattr__(mod, "asdict", asdict_adapter)
    object.__setattr__(mod, "dataclasses", _stdlib_dataclasses)

    _stdlib_dataclasses.field = field_adapter
    _stdlib_dataclasses.dataclass = dataclass_adapter

    object.__setattr__(mod, "_oneshot", Field)

    _skip_tests = {
        'test_default_value',
        'test_no_default_value',
        'test_init_var_name_shadowing',
    }
    for cls_name in dir(mod):
        cls_obj = getattr(mod, cls_name, None)
        if isinstance(cls_obj, type) and issubclass(cls_obj, unittest.TestCase):
            for skip_name in _skip_tests:
                method = getattr(cls_obj, skip_name, None)
                if method is not None:
                    setattr(cls_obj, skip_name,
                            unittest.skip("py2-specific: incompatible with stdlib adapter")(method))

    return loader.loadTestsFromModule(mod)


if __name__ == '__main__':
    unittest.main()
