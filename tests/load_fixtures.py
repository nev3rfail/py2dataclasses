"""Tests for load/loads/dump/dumps functionality."""
from __future__ import print_function
import sys
import json
import six

import unittest

from dataclasses import (
    dataclass, field, load, loads, dump, dumps,
    validate, validates, InitVar, ValidationError, RAISE, EXCLUDE,
)
from typing import (
    ClassVar, List, Dict, Tuple, Optional, Any, TypeVar, Generic, Set, Union,
    Callable,
)


_validation_side_effects = []
_validation_default_factory_calls = []


class _BytesSerializer(object):
    dump_kwargs = None
    load_kwargs = None

    @classmethod
    def dumps(cls, data, **kwargs):
        cls.dump_kwargs = kwargs
        return b'packed:' + json.dumps(data, sort_keys=True).encode('utf-8')

    @classmethod
    def loads(cls, payload, **kwargs):
        cls.load_kwargs = kwargs
        prefix = b'packed:'
        if not payload.startswith(prefix):
            raise ValueError('invalid payload')
        return json.loads(payload[len(prefix):].decode('utf-8'))


def _record_validation_side_effect(value):
    _validation_side_effects.append(value)


def _validation_default_factory():
    _validation_default_factory_calls.append('factory')
    return 1


# ---------------------------------------------------------------------------
# Test dataclass definitions
# ---------------------------------------------------------------------------

@dataclass
class Point(object):
    x = field(int)
    y = field(int)


@dataclass
class User(object):
    name = field(str)
    age = field(int)


@dataclass
class Address(object):
    city = field(str)
    zip_code = field(str)


@dataclass
class UserWithAddress(object):
    name = field(str)
    address = field(Address)


@dataclass
class WithDefaults(object):
    name = field(str)
    score = field(int, default=0)
    tags = field(list, default_factory=list)


@dataclass
class WithOptional(object):
    name = field(str)
    nickname = field(Optional[str], default=None)


@dataclass
class WithList(object):
    values = field(List[int])


@dataclass
class WithDict(object):
    mapping = field(Dict[str, int])


@dataclass
class WithTuple(object):
    pair = field(Tuple[int, str])


@dataclass
class WithVarTuple(object):
    values = field(Tuple[int, ...])


@dataclass
class WithNestedList(object):
    users = field(List[User])


@dataclass
class DeeplyNested(object):
    name = field(str)
    groups = field(List[UserWithAddress])


@dataclass
class WithNestedListOfLists(object):
    matrix = field(List[List[int]])


@dataclass
class WithListOfDicts(object):
    records = field(List[Dict[str, int]])


@dataclass
class WithDictOfLists(object):
    groups = field(Dict[str, List[int]])


@dataclass
class WithListOfTuples(object):
    pairs = field(List[Tuple[str, int]])


@dataclass
class WithDictOfDataclasses(object):
    users = field(Dict[str, User])


@dataclass
class WithListOfOptional(object):
    values = field(List[Optional[int]])


@dataclass
class WithSet(object):
    values = field(Set[int])


@dataclass
class WithUnion(object):
    value = field(Union[int, str])


@dataclass
class WithAny(object):
    data = field(Any)


@dataclass
class WithFloat(object):
    value = field(float)


@dataclass
class WithBool(object):
    flag = field(bool)


@dataclass
class WithStringType(object):
    value = field('int')


@dataclass
class WithUnresolvedType(object):
    value = field('MissingAnnotation')


@dataclass
class WithCallableType(object):
    callback = field(Callable[[int], str])


@dataclass
class WithClassVar(object):
    class_val = field(ClassVar[int], 10)
    x = field(int)


@dataclass
class WithInitVar(object):
    x = field(int)
    scale = field(InitVar[int], default=1)

    def __post_init__(self, scale):
        self.x *= scale


@dataclass
class WithInitVarRequired(object):
    x = field(int)
    multiplier = field(InitVar[int])

    def __post_init__(self, multiplier):
        self.x *= multiplier


@dataclass
class WithInitFalse(object):
    x = field(int)
    y = field(int, init=False)

    def __post_init__(self):
        self.y = self.x * 2


@dataclass
class WithClassVarAndInitVar(object):
    class_name = field(ClassVar[str], 'MyClass')
    x = field(int)
    scale = field(InitVar[int], default=1)
    computed = field(int, init=False)

    def __post_init__(self, scale):
        self.computed = self.x * scale


T = TypeVar('T')
U = TypeVar('U')


@dataclass
class Box(Generic[T]):
    value = field(T)


@dataclass
class Pair(Generic[T, U]):
    first = field(T)
    second = field(U)


@dataclass
class GenericList(Generic[T]):
    items = field(List[T])


@dataclass
class GenericDict(Generic[T]):
    mapping = field(Dict[str, T])


@dataclass
class GenericNested(Generic[T]):
    name = field(str)
    box = field(Box)


@dataclass
class GenericAliasFields(Generic[T]):
    box = field(Box[T])
    boxes = field(List[Box[T]])
    mapping = field(Dict[str, Box[T]])


@dataclass
class GenericOptionalUnion(Generic[T]):
    maybe = field(Optional[T])
    either = field(Union[T, str])


@dataclass
class StringGenericAnnotations(Generic[T]):
    item = field('T')
    maybe = field('Optional[T]')
    box = field('Box[T]')
    boxes = field('List[Box[T]]')


@dataclass
class WithParameterizedBox(object):
    box = field(Box[int])


@dataclass
class WithParameterizedBoxList(object):
    boxes = field(List[Box[int]])


@dataclass
class WithParameterizedBoxDict(object):
    boxes = field(Dict[str, Box[int]])


@dataclass
class WithParameterizedUserBox(object):
    box = field(Box[User])


# --- Generic inheritance (auto-resolution) ---

@dataclass
class TypedBox(Generic[T]):
    value = field(T)


@dataclass
class IntBox(TypedBox[int]):
    pass


@dataclass
class StrBox(TypedBox[str]):
    pass


@dataclass
class ListBoxWithOwn(TypedBox[List[T]], Generic[T]):
    item = field(T)


@dataclass
class IntListBoxWithOwn(ListBoxWithOwn[int]):
    pass


V = TypeVar('V')


@dataclass
class TypedPair(Generic[T, V]):
    first = field(T)
    second = field(V)


@dataclass
class IntStrPair(TypedPair[int, str]):
    pass


@dataclass
class SwappedPair(TypedPair[V, T], Generic[T, V]):
    pass


@dataclass
class SwappedIntStrPair(SwappedPair[int, str]):
    pass


@dataclass
class TypedContainer(Generic[T]):
    items = field(List[T])


@dataclass
class IntContainer(TypedContainer[int]):
    pass


@dataclass
class TypedBoxWithExtra(Generic[T]):
    value = field(T)
    label = field(str)


@dataclass
class IntBoxWithExtra(TypedBoxWithExtra[int]):
    pass


# --- Bound TypeVar ---

class Animal(object):
    def __init__(self, name):
        self.name = name


class Dog(Animal):
    pass


class Cat(Animal):
    pass


BoundT = TypeVar('BoundT', bound=Animal)


@dataclass
class Shelter(Generic[BoundT]):
    pet = field(BoundT)


BoundIntT = TypeVar('BoundIntT', bound=int)


@dataclass
class BoundIntBox(Generic[BoundIntT]):
    value = field(BoundIntT)


# --- Constrained TypeVar ---

CT = TypeVar('CT', int, str)


@dataclass
class ConstrainedBox(Generic[CT]):
    value = field(CT)


@dataclass
class ConstrainedList(Generic[CT]):
    items = field(List[CT])


# ---------------------------------------------------------------------------

__all__ = [name for name in list(globals()) if not name.startswith('__')]
