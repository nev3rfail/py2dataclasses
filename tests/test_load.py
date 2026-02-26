"""Tests for load/loads/dump/dumps functionality."""
from __future__ import print_function
import os
import sys
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import unittest

from dataclasses import (
    dataclass, field, fields, asdict, load, loads, dump, dumps,
    is_dataclass, InitVar, MISSING,
)
from typing import ClassVar, List, Dict, Tuple, Optional, Any, TypeVar, Generic


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
class WithAny(object):
    data = field(Any)


@dataclass
class WithFloat(object):
    value = field(float)


@dataclass
class WithBool(object):
    flag = field(bool)


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
class Box(object):
    value = field(T)


@dataclass
class Pair(object):
    first = field(T)
    second = field(U)


@dataclass
class GenericList(object):
    items = field(List[T])


@dataclass
class GenericDict(object):
    mapping = field(Dict[str, T])


@dataclass
class GenericNested(object):
    name = field(str)
    box = field(Box)


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


V = TypeVar('V')


@dataclass
class TypedPair(Generic[T, V]):
    first = field(T)
    second = field(V)


@dataclass
class IntStrPair(TypedPair[int, str]):
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
class Shelter(object):
    pet = field(BoundT)


BoundIntT = TypeVar('BoundIntT', bound=int)


@dataclass
class BoundIntBox(object):
    value = field(BoundIntT)


# --- Constrained TypeVar ---

CT = TypeVar('CT', int, str)


@dataclass
class ConstrainedBox(object):
    value = field(CT)


@dataclass
class ConstrainedList(object):
    items = field(List[CT])


# ---------------------------------------------------------------------------
# Tests: basic load
# ---------------------------------------------------------------------------

class TestLoadBasic(unittest.TestCase):

    def test_load_simple(self):
        p = load(Point, {'x': 1, 'y': 2})
        self.assertEqual(p.x, 1)
        self.assertEqual(p.y, 2)

    def test_load_classmethod(self):
        p = Point.load({'x': 3, 'y': 4})
        self.assertEqual(p.x, 3)
        self.assertEqual(p.y, 4)

    def test_loads_simple(self):
        p = loads(Point, '{"x": 10, "y": 20}')
        self.assertEqual(p.x, 10)
        self.assertEqual(p.y, 20)

    def test_loads_classmethod(self):
        p = Point.loads('{"x": 10, "y": 20}')
        self.assertEqual(p.x, 10)
        self.assertEqual(p.y, 20)

    def test_load_with_defaults(self):
        obj = load(WithDefaults, {'name': 'test'})
        self.assertEqual(obj.name, 'test')
        self.assertEqual(obj.score, 0)
        self.assertEqual(obj.tags, [])

    def test_load_override_defaults(self):
        obj = load(WithDefaults, {'name': 'test', 'score': 99, 'tags': [1, 2]})
        self.assertEqual(obj.score, 99)
        self.assertEqual(obj.tags, [1, 2])

    def test_load_default_factory_isolation(self):
        obj1 = load(WithDefaults, {'name': 'a'})
        obj2 = load(WithDefaults, {'name': 'b'})
        obj1.tags.append('x')
        self.assertEqual(obj1.tags, ['x'])
        self.assertEqual(obj2.tags, [])

    def test_load_missing_required_field(self):
        with self.assertRaises(ValueError):
            load(Point, {'x': 1})

    def test_load_not_a_dataclass(self):
        with self.assertRaises(TypeError):
            load(int, {'x': 1})

    def test_load_data_not_dict(self):
        with self.assertRaises(TypeError):
            load(Point, [1, 2])

    def test_load_extra_keys_ignored(self):
        p = load(Point, {'x': 1, 'y': 2, 'z': 3})
        self.assertEqual(p.x, 1)
        self.assertEqual(p.y, 2)

    def test_load_extra_keys_strict(self):
        with self.assertRaises(TypeError):
            load(Point, {'x': 1, 'y': 2, 'z': 3}, strict=True)


# ---------------------------------------------------------------------------
# Tests: type validation
# ---------------------------------------------------------------------------

class TestValidation(unittest.TestCase):

    def test_wrong_type_int_gets_str(self):
        with self.assertRaises(TypeError):
            load(Point, {'x': 'not_int', 'y': 2})

    def test_wrong_type_str_gets_int(self):
        with self.assertRaises(TypeError):
            load(User, {'name': 123, 'age': 25})

    def test_bool_not_accepted_as_int(self):
        with self.assertRaises(TypeError):
            load(Point, {'x': True, 'y': 2})

    def test_int_to_float_coercion(self):
        obj = load(WithFloat, {'value': 42})
        self.assertIsInstance(obj.value, float)
        self.assertEqual(obj.value, 42.0)

    def test_float_stays_float(self):
        obj = load(WithFloat, {'value': 3.14})
        self.assertEqual(obj.value, 3.14)

    def test_bool_not_accepted_as_float(self):
        with self.assertRaises(TypeError):
            load(WithFloat, {'value': True})

    def test_bool_valid(self):
        obj = load(WithBool, {'flag': True})
        self.assertTrue(obj.flag)

    def test_none_for_required_field(self):
        with self.assertRaises(TypeError):
            load(Point, {'x': None, 'y': 2})

    def test_none_for_optional_field(self):
        obj = load(WithOptional, {'name': 'test', 'nickname': None})
        self.assertIsNone(obj.nickname)

    def test_optional_with_value(self):
        obj = load(WithOptional, {'name': 'test', 'nickname': 'nick'})
        self.assertEqual(obj.nickname, 'nick')

    def test_optional_missing_uses_default(self):
        obj = load(WithOptional, {'name': 'test'})
        self.assertIsNone(obj.nickname)

    def test_any_accepts_anything(self):
        obj = load(WithAny, {'data': 42})
        self.assertEqual(obj.data, 42)
        obj = load(WithAny, {'data': 'string'})
        self.assertEqual(obj.data, 'string')
        obj = load(WithAny, {'data': [1, 2, 3]})
        self.assertEqual(obj.data, [1, 2, 3])


# ---------------------------------------------------------------------------
# Tests: nested dataclasses
# ---------------------------------------------------------------------------

class TestNested(unittest.TestCase):

    def test_nested_dataclass(self):
        data = {'name': 'John', 'address': {'city': 'NYC', 'zip_code': '10001'}}
        obj = load(UserWithAddress, data)
        self.assertEqual(obj.name, 'John')
        self.assertIsInstance(obj.address, Address)
        self.assertEqual(obj.address.city, 'NYC')
        self.assertEqual(obj.address.zip_code, '10001')

    def test_deeply_nested(self):
        data = {
            'name': 'group1',
            'groups': [
                {
                    'name': 'Alice',
                    'address': {'city': 'NYC', 'zip_code': '10001'}
                },
                {
                    'name': 'Bob',
                    'address': {'city': 'LA', 'zip_code': '90001'}
                },
            ]
        }
        obj = load(DeeplyNested, data)
        self.assertEqual(obj.name, 'group1')
        self.assertEqual(len(obj.groups), 2)
        self.assertIsInstance(obj.groups[0], UserWithAddress)
        self.assertEqual(obj.groups[0].address.city, 'NYC')
        self.assertEqual(obj.groups[1].name, 'Bob')

    def test_nested_wrong_type(self):
        data = {'name': 'John', 'address': 'not_a_dict'}
        with self.assertRaises(TypeError):
            load(UserWithAddress, data)

    def test_nested_inner_validation(self):
        data = {'name': 'John', 'address': {'city': 123, 'zip_code': '10001'}}
        with self.assertRaises(TypeError):
            load(UserWithAddress, data)


# ---------------------------------------------------------------------------
# Tests: generic types
# ---------------------------------------------------------------------------

class TestGenerics(unittest.TestCase):

    def test_list_of_int(self):
        obj = load(WithList, {'values': [1, 2, 3]})
        self.assertEqual(obj.values, [1, 2, 3])

    def test_list_of_int_wrong_element(self):
        with self.assertRaises(TypeError):
            load(WithList, {'values': [1, 'two', 3]})

    def test_list_not_a_list(self):
        with self.assertRaises(TypeError):
            load(WithList, {'values': 'not_a_list'})

    def test_dict_str_int(self):
        obj = load(WithDict, {'mapping': {'a': 1, 'b': 2}})
        self.assertEqual(obj.mapping, {'a': 1, 'b': 2})

    def test_dict_wrong_value_type(self):
        with self.assertRaises(TypeError):
            load(WithDict, {'mapping': {'a': 'not_int'}})

    def test_tuple_from_list(self):
        obj = load(WithTuple, {'pair': [42, 'hello']})
        self.assertIsInstance(obj.pair, tuple)
        self.assertEqual(obj.pair, (42, 'hello'))

    def test_tuple_wrong_length(self):
        with self.assertRaises(TypeError):
            load(WithTuple, {'pair': [1, 'a', 'extra']})

    def test_tuple_wrong_element_type(self):
        with self.assertRaises(TypeError):
            load(WithTuple, {'pair': ['not_int', 'hello']})

    def test_list_of_dataclass(self):
        data = {'users': [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]}
        obj = load(WithNestedList, data)
        self.assertEqual(len(obj.users), 2)
        self.assertIsInstance(obj.users[0], User)
        self.assertEqual(obj.users[0].name, 'Alice')
        self.assertEqual(obj.users[1].age, 25)

    def test_empty_list(self):
        obj = load(WithList, {'values': []})
        self.assertEqual(obj.values, [])

    def test_empty_dict(self):
        obj = load(WithDict, {'mapping': {}})
        self.assertEqual(obj.mapping, {})


# ---------------------------------------------------------------------------
# Tests: nested collections (List[List[...]], Dict[str, List[...]], etc.)
# ---------------------------------------------------------------------------

class TestNestedCollections(unittest.TestCase):

    def test_list_of_lists(self):
        data = {'matrix': [[1, 2], [3, 4], [5, 6]]}
        obj = load(WithNestedListOfLists, data)
        self.assertEqual(obj.matrix, [[1, 2], [3, 4], [5, 6]])

    def test_list_of_lists_wrong_inner_type(self):
        with self.assertRaises(TypeError):
            load(WithNestedListOfLists, {'matrix': [[1, 'bad'], [3, 4]]})

    def test_list_of_lists_inner_not_list(self):
        with self.assertRaises(TypeError):
            load(WithNestedListOfLists, {'matrix': [1, 2, 3]})

    def test_list_of_lists_empty(self):
        obj = load(WithNestedListOfLists, {'matrix': []})
        self.assertEqual(obj.matrix, [])

    def test_list_of_lists_empty_inner(self):
        obj = load(WithNestedListOfLists, {'matrix': [[], [1]]})
        self.assertEqual(obj.matrix, [[], [1]])

    def test_list_of_dicts(self):
        data = {'records': [{'a': 1, 'b': 2}, {'c': 3}]}
        obj = load(WithListOfDicts, data)
        self.assertEqual(obj.records, [{'a': 1, 'b': 2}, {'c': 3}])

    def test_list_of_dicts_wrong_value(self):
        with self.assertRaises(TypeError):
            load(WithListOfDicts, {'records': [{'a': 'not_int'}]})

    def test_list_of_dicts_inner_not_dict(self):
        with self.assertRaises(TypeError):
            load(WithListOfDicts, {'records': ['not_a_dict']})

    def test_dict_of_lists(self):
        data = {'groups': {'evens': [2, 4, 6], 'odds': [1, 3, 5]}}
        obj = load(WithDictOfLists, data)
        self.assertEqual(obj.groups, {'evens': [2, 4, 6], 'odds': [1, 3, 5]})

    def test_dict_of_lists_wrong_element(self):
        with self.assertRaises(TypeError):
            load(WithDictOfLists, {'groups': {'a': [1, 'bad']}})

    def test_dict_of_lists_value_not_list(self):
        with self.assertRaises(TypeError):
            load(WithDictOfLists, {'groups': {'a': 'not_list'}})

    def test_list_of_tuples(self):
        data = {'pairs': [['alice', 1], ['bob', 2]]}
        obj = load(WithListOfTuples, data)
        self.assertEqual(obj.pairs, [('alice', 1), ('bob', 2)])
        self.assertIsInstance(obj.pairs[0], tuple)

    def test_list_of_tuples_wrong_inner(self):
        with self.assertRaises(TypeError):
            load(WithListOfTuples, {'pairs': [['alice', 'not_int']]})

    def test_dict_of_dataclasses(self):
        data = {'users': {
            'alice': {'name': 'Alice', 'age': 30},
            'bob': {'name': 'Bob', 'age': 25},
        }}
        obj = load(WithDictOfDataclasses, data)
        self.assertEqual(len(obj.users), 2)
        self.assertIsInstance(obj.users['alice'], User)
        self.assertEqual(obj.users['alice'].name, 'Alice')
        self.assertEqual(obj.users['bob'].age, 25)

    def test_dict_of_dataclasses_wrong_value(self):
        with self.assertRaises(TypeError):
            load(WithDictOfDataclasses, {'users': {'alice': 'not_a_dict'}})

    def test_list_of_optional(self):
        data = {'values': [1, None, 3, None]}
        obj = load(WithListOfOptional, data)
        self.assertEqual(obj.values, [1, None, 3, None])

    def test_list_of_optional_wrong_type(self):
        with self.assertRaises(TypeError):
            load(WithListOfOptional, {'values': [1, 'bad', 3]})

    def test_roundtrip_nested_collections(self):
        obj = WithNestedListOfLists(matrix=[[1, 2], [3, 4]])
        obj2 = WithNestedListOfLists.loads(obj.dumps())
        self.assertEqual(obj, obj2)

    def test_roundtrip_dict_of_lists(self):
        obj = WithDictOfLists(groups={'a': [1, 2], 'b': [3]})
        obj2 = WithDictOfLists.loads(obj.dumps())
        self.assertEqual(obj, obj2)

    def test_roundtrip_dict_of_dataclasses(self):
        obj = WithDictOfDataclasses(users={
            'a': User('Alice', 30),
            'b': User('Bob', 25),
        })
        obj2 = load(WithDictOfDataclasses, dump(obj))
        self.assertEqual(obj, obj2)

    def test_nested_error_path_list_of_lists(self):
        try:
            load(WithNestedListOfLists, {'matrix': [[1, 2], [3, 'bad']]})
            self.fail('Expected TypeError')
        except TypeError as e:
            msg = str(e)
            self.assertIn('matrix[1]', msg)

    def test_nested_error_path_dict_of_lists(self):
        try:
            load(WithDictOfLists, {'groups': {'evens': [2, 'bad']}})
            self.fail('Expected TypeError')
        except TypeError as e:
            msg = str(e)
            self.assertIn('groups', msg)

    def test_nested_error_path_dict_of_dataclasses(self):
        try:
            load(WithDictOfDataclasses, {
                'users': {'alice': {'name': 123, 'age': 30}}
            })
            self.fail('Expected TypeError')
        except TypeError as e:
            msg = str(e)
            self.assertIn('name', msg)
            self.assertIn('str', msg)


# ---------------------------------------------------------------------------
# Tests: ClassVar, InitVar, init=False
# ---------------------------------------------------------------------------

class TestClassVarInitVar(unittest.TestCase):

    # --- ClassVar ---

    def test_classvar_skipped_on_load(self):
        obj = load(WithClassVar, {'x': 42})
        self.assertEqual(obj.x, 42)
        self.assertEqual(WithClassVar.class_val, 10)

    def test_classvar_in_data_ignored(self):
        obj = load(WithClassVar, {'x': 42, 'class_val': 999})
        self.assertEqual(obj.x, 42)
        # ClassVar stays at class-level default, not overwritten
        self.assertEqual(WithClassVar.class_val, 10)

    def test_classvar_in_data_strict_ignored(self):
        # ClassVar keys are not "extra" -- they are just skipped
        obj = load(WithClassVar, {'x': 42, 'class_val': 999}, strict=True)
        self.assertEqual(obj.x, 42)

    def test_classvar_not_in_fields(self):
        from dataclasses import fields as dc_fields
        fs = dc_fields(WithClassVar)
        names = [f.name for f in fs]
        self.assertNotIn('class_val', names)
        self.assertIn('x', names)

    # --- InitVar ---

    def test_initvar_with_value(self):
        obj = load(WithInitVar, {'x': 5, 'scale': 3})
        self.assertEqual(obj.x, 15)

    def test_initvar_uses_default(self):
        obj = load(WithInitVar, {'x': 5})
        self.assertEqual(obj.x, 5)  # scale defaults to 1

    def test_initvar_required_present(self):
        obj = load(WithInitVarRequired, {'x': 5, 'multiplier': 4})
        self.assertEqual(obj.x, 20)

    def test_initvar_required_missing(self):
        with self.assertRaises(ValueError):
            load(WithInitVarRequired, {'x': 5})

    @unittest.skipIf(sys.version_info >= (3,), "InitVar type validation differs on Python 3")
    def test_initvar_type_validated(self):
        with self.assertRaises(TypeError):
            load(WithInitVar, {'x': 5, 'scale': 'not_int'})

    def test_initvar_not_in_fields(self):
        from dataclasses import fields as dc_fields
        obj = load(WithInitVar, {'x': 5, 'scale': 3})
        # InitVar is not in fields() output (not a stored field)
        names = [f.name for f in dc_fields(obj)]
        self.assertNotIn('scale', names)

    # --- init=False ---

    def test_init_false_computed(self):
        obj = load(WithInitFalse, {'x': 5})
        self.assertEqual(obj.x, 5)
        self.assertEqual(obj.y, 10)  # set by __post_init__

    def test_init_false_in_data_ignored(self):
        # y is in the data but init=False, so it's ignored (non-strict)
        obj = load(WithInitFalse, {'x': 5, 'y': 999})
        self.assertEqual(obj.y, 10)  # __post_init__ sets it, not the data

    def test_init_false_in_data_strict_raises(self):
        with self.assertRaises(TypeError):
            load(WithInitFalse, {'x': 5, 'y': 999}, strict=True)

    # --- Combined ClassVar + InitVar + init=False ---

    def test_combined_classvar_initvar_initfalse(self):
        obj = load(WithClassVarAndInitVar, {'x': 5, 'scale': 3})
        self.assertEqual(obj.x, 5)
        self.assertEqual(obj.computed, 15)  # x * scale via __post_init__
        self.assertEqual(WithClassVarAndInitVar.class_name, 'MyClass')

    def test_combined_defaults(self):
        obj = load(WithClassVarAndInitVar, {'x': 7})
        self.assertEqual(obj.x, 7)
        self.assertEqual(obj.computed, 7)  # scale defaults to 1

    def test_combined_dump_excludes_initvar(self):
        obj = load(WithClassVarAndInitVar, {'x': 5, 'scale': 3})
        d = dump(obj)
        self.assertIn('x', d)
        self.assertIn('computed', d)
        self.assertNotIn('scale', d)       # InitVar not stored
        self.assertNotIn('class_name', d)  # ClassVar not in fields

    def test_combined_loads_json(self):
        obj = WithClassVarAndInitVar.loads('{"x": 10, "scale": 2}')
        self.assertEqual(obj.x, 10)
        self.assertEqual(obj.computed, 20)


# ---------------------------------------------------------------------------
# Tests: TypeVar / generics with type_vars
# ---------------------------------------------------------------------------

class TestTypeVars(unittest.TestCase):

    # --- Without type_vars: TypeVar fields skip validation ---

    def test_typevar_no_binding_accepts_anything(self):
        obj = load(Box, {'value': 'hello'})
        self.assertEqual(obj.value, 'hello')
        obj2 = load(Box, {'value': 42})
        self.assertEqual(obj2.value, 42)

    def test_list_typevar_no_binding_accepts_mixed(self):
        obj = load(GenericList, {'items': [1, 'two', None]})
        self.assertEqual(obj.items, [1, 'two', None])

    # --- With type_vars: validates resolved types ---

    def test_typevar_resolved_int(self):
        obj = load(Box, {'value': 42}, type_vars={T: int})
        self.assertEqual(obj.value, 42)

    def test_typevar_resolved_str(self):
        obj = load(Box, {'value': 'hello'}, type_vars={T: str})
        self.assertEqual(obj.value, 'hello')

    def test_typevar_resolved_rejects_wrong_type(self):
        with self.assertRaises(TypeError):
            load(Box, {'value': 'bad'}, type_vars={T: int})

    def test_typevar_resolved_rejects_none(self):
        with self.assertRaises(TypeError):
            load(Box, {'value': None}, type_vars={T: int})

    def test_typevar_resolved_optional(self):
        obj = load(Box, {'value': None}, type_vars={T: Optional[int]})
        self.assertIsNone(obj.value)
        obj2 = load(Box, {'value': 42}, type_vars={T: Optional[int]})
        self.assertEqual(obj2.value, 42)

    # --- Two TypeVars ---

    def test_two_typevars(self):
        obj = load(Pair, {'first': 1, 'second': 'hello'}, type_vars={T: int, U: str})
        self.assertEqual(obj.first, 1)
        self.assertEqual(obj.second, 'hello')

    def test_two_typevars_wrong_first(self):
        with self.assertRaises(TypeError):
            load(Pair, {'first': 'bad', 'second': 'ok'}, type_vars={T: int, U: str})

    def test_two_typevars_wrong_second(self):
        with self.assertRaises(TypeError):
            load(Pair, {'first': 1, 'second': 99}, type_vars={T: int, U: str})

    # --- List[T] resolved ---

    def test_list_typevar_resolved(self):
        obj = load(GenericList, {'items': [1, 2, 3]}, type_vars={T: int})
        self.assertEqual(obj.items, [1, 2, 3])

    def test_list_typevar_resolved_rejects(self):
        with self.assertRaises(TypeError):
            load(GenericList, {'items': [1, 'bad']}, type_vars={T: int})

    def test_list_typevar_resolved_empty(self):
        obj = load(GenericList, {'items': []}, type_vars={T: int})
        self.assertEqual(obj.items, [])

    # --- Dict[str, T] resolved ---

    def test_dict_typevar_resolved(self):
        obj = load(GenericDict, {'mapping': {'a': 1, 'b': 2}}, type_vars={T: int})
        self.assertEqual(obj.mapping, {'a': 1, 'b': 2})

    def test_dict_typevar_resolved_rejects(self):
        with self.assertRaises(TypeError):
            load(GenericDict, {'mapping': {'a': 'bad'}}, type_vars={T: int})

    # --- T resolved to a dataclass ---

    def test_typevar_resolved_to_dataclass(self):
        obj = load(Box, {'value': {'name': 'Alice', 'age': 30}}, type_vars={T: User})
        self.assertIsInstance(obj.value, User)
        self.assertEqual(obj.value.name, 'Alice')

    def test_list_typevar_resolved_to_dataclass(self):
        data = {'items': [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]}
        obj = load(GenericList, data, type_vars={T: User})
        self.assertEqual(len(obj.items), 2)
        self.assertIsInstance(obj.items[0], User)

    # --- Classmethod with type_vars ---

    def test_classmethod_with_type_vars(self):
        obj = Box.load({'value': 42}, type_vars={T: int})
        self.assertEqual(obj.value, 42)

    def test_classmethod_loads_with_type_vars(self):
        obj = Box.loads('{"value": 42}', type_vars={T: int})
        self.assertEqual(obj.value, 42)

    def test_classmethod_type_vars_rejects(self):
        with self.assertRaises(TypeError):
            Box.load({'value': 'bad'}, type_vars={T: int})

    # --- Error messages ---

    def test_typevar_error_message(self):
        try:
            load(Box, {'value': 'bad'}, type_vars={T: int})
            self.fail('Expected TypeError')
        except TypeError as e:
            msg = str(e)
            self.assertIn('value', msg)
            self.assertIn('int', msg)

    def test_list_typevar_error_path(self):
        try:
            load(GenericList, {'items': [1, 'bad']}, type_vars={T: int})
            self.fail('Expected TypeError')
        except TypeError as e:
            msg = str(e)
            self.assertIn('items[1]', msg)


# ---------------------------------------------------------------------------
# Tests: generic inheritance (auto-resolution from class hierarchy)
# ---------------------------------------------------------------------------

class TestGenericInheritance(unittest.TestCase):

    # --- Basic: IntBox inherits TypedBox[int] ---

    def test_int_box_accepts_int(self):
        obj = load(IntBox, {'value': 42})
        self.assertEqual(obj.value, 42)

    def test_int_box_rejects_str(self):
        with self.assertRaises(TypeError):
            load(IntBox, {'value': 'bad'})

    def test_str_box_accepts_str(self):
        obj = load(StrBox, {'value': 'hello'})
        self.assertEqual(obj.value, 'hello')

    def test_str_box_rejects_int(self):
        with self.assertRaises(TypeError):
            load(StrBox, {'value': 42})

    # --- Two TypeVars: IntStrPair inherits TypedPair[int, str] ---

    def test_int_str_pair_accepts(self):
        obj = load(IntStrPair, {'first': 1, 'second': 'hello'})
        self.assertEqual(obj.first, 1)
        self.assertEqual(obj.second, 'hello')

    def test_int_str_pair_rejects_wrong_first(self):
        with self.assertRaises(TypeError):
            load(IntStrPair, {'first': 'bad', 'second': 'ok'})

    def test_int_str_pair_rejects_wrong_second(self):
        with self.assertRaises(TypeError):
            load(IntStrPair, {'first': 1, 'second': 99})

    # --- Generic container: IntContainer inherits TypedContainer[int] -> List[int] ---

    def test_int_container_accepts(self):
        obj = load(IntContainer, {'items': [1, 2, 3]})
        self.assertEqual(obj.items, [1, 2, 3])

    def test_int_container_rejects_wrong_element(self):
        with self.assertRaises(TypeError):
            load(IntContainer, {'items': [1, 'bad']})

    def test_int_container_empty(self):
        obj = load(IntContainer, {'items': []})
        self.assertEqual(obj.items, [])

    # --- Mixed fields: IntBoxWithExtra has T=int + regular str ---

    def test_mixed_fields(self):
        obj = load(IntBoxWithExtra, {'value': 42, 'label': 'test'})
        self.assertEqual(obj.value, 42)
        self.assertEqual(obj.label, 'test')

    def test_mixed_fields_rejects_wrong_generic(self):
        with self.assertRaises(TypeError):
            load(IntBoxWithExtra, {'value': 'bad', 'label': 'test'})

    def test_mixed_fields_rejects_wrong_regular(self):
        with self.assertRaises(TypeError):
            load(IntBoxWithExtra, {'value': 42, 'label': 123})

    # --- Explicit type_vars override inferred ---

    def test_explicit_overrides_inferred(self):
        # IntBox infers T=int, but explicit type_vars={T: str} should override
        obj = load(IntBox, {'value': 'hello'}, type_vars={T: str})
        self.assertEqual(obj.value, 'hello')

    # --- Classmethod works with auto-resolution ---

    def test_classmethod_auto_resolution(self):
        obj = IntBox.load({'value': 42})
        self.assertEqual(obj.value, 42)

    def test_classmethod_auto_resolution_rejects(self):
        with self.assertRaises(TypeError):
            IntBox.load({'value': 'bad'})

    def test_classmethod_loads_auto_resolution(self):
        obj = IntBox.loads('{"value": 42}')
        self.assertEqual(obj.value, 42)

    # --- Roundtrip ---

    def test_roundtrip_generic_inheritance(self):
        obj = IntBox(42)
        obj2 = IntBox.loads(obj.dumps())
        self.assertEqual(obj, obj2)

    # --- Parent class (still generic) works as before ---

    def test_parent_still_generic_no_validation(self):
        # TypedBox[T] without type_vars -- accepts anything
        obj = load(TypedBox, {'value': 'anything'})
        self.assertEqual(obj.value, 'anything')

    def test_parent_with_explicit_type_vars(self):
        obj = load(TypedBox, {'value': 42}, type_vars={T: int})
        self.assertEqual(obj.value, 42)


# ---------------------------------------------------------------------------
# Tests: bound TypeVar
# ---------------------------------------------------------------------------

class TestBoundTypeVar(unittest.TestCase):

    def test_bound_accepts_exact_type(self):
        a = Animal('Buddy')
        obj = load(Shelter, {'pet': a})
        self.assertIs(obj.pet, a)

    def test_bound_accepts_subclass(self):
        d = Dog('Rex')
        obj = load(Shelter, {'pet': d})
        self.assertIs(obj.pet, d)

    def test_bound_accepts_another_subclass(self):
        c = Cat('Whiskers')
        obj = load(Shelter, {'pet': c})
        self.assertIs(obj.pet, c)

    def test_bound_rejects_wrong_type(self):
        with self.assertRaises(TypeError):
            load(Shelter, {'pet': 'not an animal'})

    def test_bound_rejects_int(self):
        with self.assertRaises(TypeError):
            load(Shelter, {'pet': 42})

    def test_bound_rejects_none(self):
        with self.assertRaises(TypeError):
            load(Shelter, {'pet': None})

    def test_bound_int_accepts_int(self):
        obj = load(BoundIntBox, {'value': 42})
        self.assertEqual(obj.value, 42)

    def test_bound_int_rejects_str(self):
        with self.assertRaises(TypeError):
            load(BoundIntBox, {'value': 'bad'})

    def test_bound_int_rejects_bool(self):
        # bool is subclass of int, but our strict validation rejects bool for int
        with self.assertRaises(TypeError):
            load(BoundIntBox, {'value': True})


# ---------------------------------------------------------------------------
# Tests: constrained TypeVar
# ---------------------------------------------------------------------------

class TestConstrainedTypeVar(unittest.TestCase):

    def test_constrained_accepts_int(self):
        obj = load(ConstrainedBox, {'value': 42})
        self.assertEqual(obj.value, 42)

    def test_constrained_accepts_str(self):
        obj = load(ConstrainedBox, {'value': 'hello'})
        self.assertEqual(obj.value, 'hello')

    def test_constrained_rejects_float(self):
        with self.assertRaises(TypeError):
            load(ConstrainedBox, {'value': 3.14})

    def test_constrained_rejects_list(self):
        with self.assertRaises(TypeError):
            load(ConstrainedBox, {'value': [1, 2]})

    def test_constrained_rejects_none(self):
        with self.assertRaises(TypeError):
            load(ConstrainedBox, {'value': None})

    def test_constrained_rejects_bool(self):
        # bool is subclass of int but strict validation rejects it
        with self.assertRaises(TypeError):
            load(ConstrainedBox, {'value': True})

    def test_constrained_list_accepts_ints(self):
        obj = load(ConstrainedList, {'items': [1, 2, 3]})
        self.assertEqual(obj.items, [1, 2, 3])

    def test_constrained_list_accepts_strs(self):
        obj = load(ConstrainedList, {'items': ['a', 'b']})
        self.assertEqual(obj.items, ['a', 'b'])

    def test_constrained_list_rejects_float(self):
        with self.assertRaises(TypeError):
            load(ConstrainedList, {'items': [1, 3.14]})

    def test_constrained_error_message(self):
        try:
            load(ConstrainedBox, {'value': 3.14})
            self.fail('Expected TypeError')
        except TypeError as e:
            msg = str(e)
            self.assertIn('value', msg)
            self.assertIn('constraint', msg)


# ---------------------------------------------------------------------------
# Tests: dump / dumps
# ---------------------------------------------------------------------------

class TestDump(unittest.TestCase):

    def test_dump_simple(self):
        p = Point(1, 2)
        d = dump(p)
        self.assertEqual(d['x'], 1)
        self.assertEqual(d['y'], 2)

    def test_dump_instance_method(self):
        p = Point(1, 2)
        d = p.dump()
        self.assertEqual(d['x'], 1)
        self.assertEqual(d['y'], 2)

    def test_dumps_simple(self):
        p = Point(1, 2)
        s = dumps(p)
        parsed = json.loads(s)
        self.assertEqual(parsed['x'], 1)
        self.assertEqual(parsed['y'], 2)

    def test_dumps_instance_method(self):
        p = Point(1, 2)
        s = p.dumps()
        parsed = json.loads(s)
        self.assertEqual(parsed['x'], 1)

    def test_dump_nested(self):
        obj = UserWithAddress('John', Address('NYC', '10001'))
        d = dump(obj)
        self.assertEqual(d['address']['city'], 'NYC')


# ---------------------------------------------------------------------------
# Tests: roundtrip
# ---------------------------------------------------------------------------

class TestRoundtrip(unittest.TestCase):

    def test_roundtrip_load_dump(self):
        p = Point(42, 99)
        p2 = load(Point, dump(p))
        self.assertEqual(p, p2)

    def test_roundtrip_loads_dumps(self):
        p = Point(42, 99)
        p2 = loads(Point, dumps(p))
        self.assertEqual(p, p2)

    def test_roundtrip_nested(self):
        obj = UserWithAddress('John', Address('NYC', '10001'))
        obj2 = load(UserWithAddress, dump(obj))
        self.assertEqual(obj, obj2)

    def test_roundtrip_with_defaults(self):
        obj = WithDefaults(name='test', score=5, tags=['a', 'b'])
        obj2 = load(WithDefaults, dump(obj))
        self.assertEqual(obj, obj2)

    def test_roundtrip_classmethod(self):
        p = Point(1, 2)
        p2 = Point.loads(p.dumps())
        self.assertEqual(p, p2)


# ---------------------------------------------------------------------------
# Tests: error messages
# ---------------------------------------------------------------------------

class TestErrorMessages(unittest.TestCase):

    def test_nested_error_path(self):
        data = {'name': 'John', 'address': {'city': 123, 'zip_code': '10001'}}
        try:
            load(UserWithAddress, data)
            self.fail('Expected TypeError')
        except TypeError as e:
            msg = str(e)
            self.assertIn('address.city', msg)
            self.assertIn('str', msg)

    def test_list_element_error_path(self):
        try:
            load(WithList, {'values': [1, 'bad', 3]})
            self.fail('Expected TypeError')
        except TypeError as e:
            msg = str(e)
            self.assertIn('values[1]', msg)

    def test_missing_field_error(self):
        try:
            load(Point, {'x': 1})
            self.fail('Expected ValueError')
        except ValueError as e:
            msg = str(e)
            self.assertIn('y', msg)
            self.assertIn('Point', msg)


if __name__ == '__main__':
    unittest.main()
