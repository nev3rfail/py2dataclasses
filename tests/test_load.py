"""Tests for load/loads/dump/dumps functionality."""
from __future__ import print_function
import sys
import json
import six

import unittest

from dataclasses import (
    dataclass, field, load, loads, dump, dumps,
    validate, validates, InitVar, ValidationError,
)
from typing import (
    ClassVar, List, Dict, Tuple, Optional, Any, TypeVar, Generic, Set, Union,
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

    def test_loads_and_generated_load_delegate_to_load(self):
        import _py2dataclasses.dataclasses as impl

        original_load = impl.load
        calls = []

        def fake_load(cls, data, strict=False, type_vars=None, collect_errors=False):
            calls.append((cls, data, strict, type_vars, collect_errors))
            return cls(9, 10)

        try:
            impl.load = fake_load
            module_loads_result = loads(Point, '{"x": 3, "y": 4}')
            generated_load_result = Point.load({'x': 5, 'y': 6})
            generated_loads_result = Point.loads('{"x": 7, "y": 8}')
        finally:
            impl.load = original_load

        self.assertEqual(module_loads_result, Point(9, 10))
        self.assertEqual(generated_load_result, Point(9, 10))
        self.assertEqual(generated_loads_result, Point(9, 10))
        self.assertEqual([call[1] for call in calls], [
            {'x': 3, 'y': 4},
            {'x': 5, 'y': 6},
            {'x': 7, 'y': 8},
        ])

    def test_loads_simple(self):
        p = loads(Point, '{"x": 10, "y": 20}')
        self.assertEqual(p.x, 10)
        self.assertEqual(p.y, 20)

    def test_loads_classmethod(self):
        p = Point.loads('{"x": 10, "y": 20}')
        self.assertEqual(p.x, 10)
        self.assertEqual(p.y, 20)

    def test_loads_accepts_custom_serializer(self):
        payload = _BytesSerializer.dumps({'x': 10, 'y': 20})

        p = loads(Point, payload, serializer=_BytesSerializer, raw=False)

        self.assertEqual(p, Point(10, 20))
        self.assertEqual(_BytesSerializer.load_kwargs, {'raw': False})

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

    def test_load_nested_extra_keys_strict(self):
        with self.assertRaises(TypeError):
            load(UserWithAddress,
                 {'name': 'John',
                  'address': {'city': 'NYC', 'zip_code': '10001',
                              'extra': True}},
                 strict=True)


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

    def test_string_field_type_is_resolved(self):
        valid_data = {'value': 42}
        invalid_data = {'value': 'bad'}

        obj = load(WithStringType, valid_data)

        self.assertEqual(obj.value, 42)

        with self.assertRaises(TypeError):
            load(WithStringType, invalid_data)

        with self.assertRaises(ValidationError) as cm:
            validate(WithStringType, invalid_data, collect_errors=True)
        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['value'])

    def test_future_annotations_are_resolved(self):
        if sys.version_info < (3,):
            self.skipTest('future annotations are Python 3 only')

        namespace = {
            '__name__': __name__,
            'dataclass': dataclass,
        }
        six.exec_(
            'from __future__ import annotations\n'
            '@dataclass\n'
            'class FutureAnnotated(object):\n'
            '    value: int\n',
            namespace)
        FutureAnnotated = namespace['FutureAnnotated']
        valid_data = {'value': 42}
        invalid_data = {'value': 'bad'}

        obj = load(FutureAnnotated, valid_data)

        self.assertEqual(obj.value, 42)

        with self.assertRaises(TypeError):
            load(FutureAnnotated, invalid_data)

        with self.assertRaises(ValidationError) as cm:
            validate(FutureAnnotated, invalid_data, collect_errors=True)
        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['value'])


class TestCollectErrors(unittest.TestCase):

    def assertValidationPaths(self, func, expected_paths):
        try:
            func()
        except ValidationError as exc:
            paths = [issue.path for issue in exc.errors]
            self.assertEqual(set(paths), set(expected_paths))
            self.assertEqual(len(paths), len(expected_paths))
            self.assertIn('Validation failed with', str(exc))
            return exc
        self.fail('Expected ValidationError')

    def test_load_collects_multiple_flat_errors(self):
        data = {'name': 123, 'age': 'bad', 'extra': True}

        exc = self.assertValidationPaths(
            lambda: load(User, data, strict=True, collect_errors=True),
            ['name', 'age', 'extra'])

        self.assertEqual(exc.errors[0].path, 'name')
        self.assertIn('expected str', exc.errors[0].message)

    def test_validate_collects_missing_type_and_unknown_errors(self):
        data = {'x': 'bad', 'z': 3}

        exc = self.assertValidationPaths(
            lambda: validate(Point, data, strict=True, collect_errors=True),
            ['x', 'y', 'z'])

        messages = dict((issue.path, issue.message) for issue in exc.errors)
        self.assertIn('expected int', messages['x'])
        self.assertIn('missing required field', messages['y'])
        self.assertIn('unknown field', messages['z'])

    def test_collect_errors_nested_paths(self):
        data = {
            'name': 123,
            'groups': [
                {'name': 'John', 'address': {'city': 42}},
                {'name': 99, 'address': 'not-an-address'},
            ],
        }

        self.assertValidationPaths(
            lambda: load(DeeplyNested, data, collect_errors=True),
            [
                'name',
                'groups[0].address.city',
                'groups[0].address.zip_code',
                'groups[1].name',
                'groups[1].address',
            ])

    def test_collect_errors_nested_strict_paths(self):
        data = {
            'name': 'John',
            'address': {
                'city': 'NYC',
                'zip_code': '10001',
                'extra': True,
            },
        }

        self.assertValidationPaths(
            lambda: load(UserWithAddress, data, strict=True,
                         collect_errors=True),
            ['address.extra'])

    def test_collect_errors_nested_type_vars(self):
        data = {'name': 'nested', 'box': {'value': 'bad'}}

        self.assertValidationPaths(
            lambda: load(GenericNested, data,
                         type_vars={T: int}, collect_errors=True),
            ['box.value'])

    def test_loads_and_validates_collect_errors(self):
        invalid_payload = '{"name": 123, "age": "bad"}'
        valid_payload = '{"name": "Alice", "age": 30}'

        exc = self.assertValidationPaths(
            lambda: User.loads(invalid_payload, collect_errors=True),
            ['name', 'age'])
        validates_result = validates(User, valid_payload, collect_errors=True)

        self.assertIn(exc.errors[1].actual, ('str', 'unicode'))
        self.assertTrue(validates_result)

    def test_validates_accepts_custom_serializer(self):
        payload = _BytesSerializer.dumps({'name': 'Alice', 'age': 30})

        result = validates(User, payload, serializer=_BytesSerializer,
                           raw=False)

        self.assertTrue(result)
        self.assertEqual(_BytesSerializer.load_kwargs, {'raw': False})

    def test_collect_errors_success_still_returns_object(self):
        obj = load(Point, {'x': 1, 'y': 2}, collect_errors=True)

        self.assertEqual(obj, Point(1, 2))

    def test_collect_errors_accepts_self_mapped_constrained_typevar(self):
        obj = load(ConstrainedBox, {'value': 'ok'}, type_vars={CT: CT},
                   collect_errors=True)

        self.assertEqual(obj.value, 'ok')

    def test_collect_errors_unbound_typevar_accepts_anything(self):
        marker = object()

        obj = load(Box, {'value': marker}, collect_errors=True)

        self.assertIs(obj.value, marker)

    def test_collect_errors_optional_value(self):
        obj = load(WithOptional, {'name': 'Alice', 'nickname': 'Al'},
                   collect_errors=True)

        self.assertEqual(obj.nickname, 'Al')

    def test_collect_errors_self_mapped_constraint_path(self):
        with self.assertRaises(ValidationError) as cm:
            load(ConstrainedBox, {'value': 3.14}, type_vars={CT: CT},
                 collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['value'])

    def test_collect_errors_bound_path(self):
        with self.assertRaises(ValidationError) as bound_cm:
            load(BoundIntBox, {'value': 'bad'}, collect_errors=True)

        self.assertEqual([issue.path for issue in bound_cm.exception.errors],
                         ['value'])

    def test_collect_errors_none_path(self):
        with self.assertRaises(ValidationError) as none_cm:
            load(Point, {'x': None, 'y': 2}, collect_errors=True)

        self.assertEqual([issue.path for issue in none_cm.exception.errors],
                         ['x'])

    def test_collect_errors_top_level_non_mapping_path(self):
        with self.assertRaises(ValidationError) as top_level:
            validate(Point, [], collect_errors=True)

        self.assertEqual(top_level.exception.errors[0].path, '')

    def test_collect_errors_ignores_classvar(self):
        result = validate(WithClassVar, {'x': 1}, collect_errors=True)

        self.assertTrue(result)

    def test_collect_errors_applies_defaults(self):
        obj = load(WithDefaults, {'name': 'defaulted'},
                   collect_errors=True)

        self.assertEqual(obj.score, 0)
        self.assertEqual(obj.tags, [])

    def test_collect_errors_init_false_strict_path(self):
        with self.assertRaises(ValidationError) as init_false:
            load(WithInitFalse, {'x': 1, 'y': 2}, strict=True,
                 collect_errors=True)

        self.assertEqual([issue.path for issue in init_false.exception.errors],
                         ['y'])

    def test_validate_rejects_non_dataclass(self):
        with self.assertRaises(TypeError):
            validate(int, {'x': 1})

    def test_collect_errors_accepts_existing_nested_dataclass(self):
        address = Address('NYC', '10001')

        obj = load(UserWithAddress,
                   {'name': 'Bob', 'address': address},
                   collect_errors=True)

        self.assertIs(obj.address, address)

    def test_collect_errors_accepts_top_level_non_instance_validation(self):
        result = validate(Point, {'x': 1, 'y': 2}, collect_errors=True)

        self.assertTrue(result)

    def test_default_validation_remains_fail_fast(self):
        with self.assertRaises(TypeError):
            load(User, {'name': 123, 'age': 'bad'})

    def test_validate_does_not_create_instances(self):
        _validation_side_effects[:] = []

        @dataclass
        class SideEffect(object):
            x = field(int)

            def __post_init__(self):
                _record_validation_side_effect(self.x)

        @dataclass
        class Wrapper(object):
            child = field(SideEffect)

        validate_result = validate(Wrapper, {'child': {'x': 1}})
        collect_result = validate(Wrapper, {'child': {'x': 2}},
                                  collect_errors=True)

        self.assertTrue(validate_result)
        self.assertTrue(collect_result)
        self.assertEqual(_validation_side_effects, [])

        loaded = load(Wrapper, {'child': {'x': 3}})

        self.assertEqual(loaded.child.x, 3)
        self.assertEqual(_validation_side_effects, [3])

    def test_validate_does_not_call_default_factory(self):
        _validation_default_factory_calls[:] = []

        @dataclass
        class WithFactory(object):
            x = field(int)
            y = field(int, default_factory=_validation_default_factory)

        validate_result = validate(WithFactory, {'x': 1})
        collect_result = validate(WithFactory, {'x': 2}, collect_errors=True)

        self.assertTrue(validate_result)
        self.assertTrue(collect_result)
        self.assertEqual(_validation_default_factory_calls, [])

        loaded = load(WithFactory, {'x': 3})

        self.assertEqual(loaded.y, 1)
        self.assertEqual(_validation_default_factory_calls, ['factory'])


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

    def test_variadic_tuple_from_list(self):
        obj = load(WithVarTuple, {'values': [1, 2, 3]})
        self.assertIsInstance(obj.values, tuple)
        self.assertEqual(obj.values, (1, 2, 3))

    def test_variadic_tuple_wrong_element_type(self):
        with self.assertRaises(TypeError):
            load(WithVarTuple, {'values': [1, 'bad', 3]})

    def test_variadic_tuple_collects_element_path(self):
        with self.assertRaises(ValidationError) as cm:
            validate(WithVarTuple, {'values': [1, 'bad', False]},
                     collect_errors=True)

        self.assertEqual(
            [issue.path for issue in cm.exception.errors],
            ['values[1]', 'values[2]'])

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

    def test_tuple_rejects_non_sequence(self):
        with self.assertRaises(TypeError):
            load(WithTuple, {'pair': 'not-a-tuple'})

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

    def test_set_generic_accepts_sequence(self):
        obj = load(WithSet, {'values': [1, 2, 2]})

        self.assertEqual(obj.values, set([1, 2]))

    def test_set_generic_rejects_non_sequence(self):
        with self.assertRaises(TypeError):
            load(WithSet, {'values': 'not-a-set'})

    def test_set_generic_rejects_wrong_element(self):
        with self.assertRaises(TypeError):
            load(WithSet, {'values': [1, 'bad']})

    def test_union_generic_accepts_first_type(self):
        obj = load(WithUnion, {'value': 42})

        self.assertEqual(obj.value, 42)

    def test_union_generic_accepts_second_type(self):
        obj = load(WithUnion, {'value': 'forty-two'})

        self.assertEqual(obj.value, 'forty-two')

    def test_union_generic_rejects_unknown_type(self):
        with self.assertRaises(TypeError):
            load(WithUnion, {'value': 3.14})

    def test_nested_dataclass_instance_passthrough(self):
        address = Address('NYC', '10001')

        obj = load(UserWithAddress, {'name': 'Bob', 'address': address})

        self.assertIs(obj.address, address)

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
        with self.assertRaises(TypeError) as cm:
            load(WithNestedListOfLists, {'matrix': [[1, 2], [3, 'bad']]})

        self.assertIn('matrix[1]', str(cm.exception))

    def test_nested_error_path_dict_of_lists(self):
        with self.assertRaises(TypeError) as cm:
            load(WithDictOfLists, {'groups': {'evens': [2, 'bad']}})

        self.assertIn('groups', str(cm.exception))

    def test_nested_error_path_dict_of_dataclasses(self):
        with self.assertRaises(TypeError) as cm:
            load(WithDictOfDataclasses, {
                'users': {'alice': {'name': 123, 'age': 30}}
            })

        msg = str(cm.exception)
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

    def test_parameterized_dataclass_alias_top_level(self):
        obj = load(Box[int], {'value': 42})
        obj2 = loads(Box[int], '{"value": 7}')
        validate_result = validate(Box[int], {'value': 99})
        validates_result = validates(Box[int], '{"value": 100}')

        self.assertIsInstance(obj, Box)
        self.assertEqual(obj.value, 42)
        self.assertEqual(obj2.value, 7)
        self.assertTrue(validate_result)
        self.assertTrue(validates_result)

    def test_parameterized_dataclass_alias_top_level_rejects(self):
        with self.assertRaises(TypeError):
            load(Box[int], {'value': 'bad'})

        with self.assertRaises(ValidationError) as cm:
            validate(Box[int], {'value': 'bad'}, collect_errors=True)
        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['value'])

    def test_future_annotations_preserve_type_vars(self):
        if sys.version_info < (3,):
            self.skipTest('future annotations are Python 3 only')

        sentinel = object()
        names = ('FutureLoadT', 'FutureBox', 'FutureListBox',
                 'FutureOptionalBox')
        previous = dict((name, globals().get(name, sentinel)) for name in names)
        try:
            six.exec_(
                'from __future__ import annotations\n'
                'FutureLoadT = TypeVar("FutureLoadT")\n'
                '@dataclass\n'
                'class FutureBox(Generic[FutureLoadT]):\n'
                '    value: FutureLoadT\n'
                '@dataclass\n'
                'class FutureListBox(Generic[FutureLoadT]):\n'
                '    items: List[FutureLoadT]\n'
                '@dataclass\n'
                'class FutureOptionalBox(Generic[FutureLoadT]):\n'
                '    maybe: Optional[FutureLoadT]\n',
                globals())
            FutureBox = globals()['FutureBox']
            FutureListBox = globals()['FutureListBox']
            FutureOptionalBox = globals()['FutureOptionalBox']
            FutureT = globals()['FutureLoadT']

            obj = load(FutureBox[int], {'value': 42})
            explicit_obj = load(FutureBox, {'value': 7},
                                type_vars={FutureT: int})
            list_obj = load(FutureListBox[int], {'items': [1, 2]})
            optional_obj = load(FutureOptionalBox[int], {'maybe': None})

            self.assertEqual(obj.value, 42)
            self.assertEqual(explicit_obj.value, 7)
            self.assertEqual(list_obj.items, [1, 2])
            self.assertIsNone(optional_obj.maybe)

            with self.assertRaises(TypeError):
                load(FutureBox[int], {'value': 'bad'})

            with self.assertRaises(TypeError):
                load(FutureBox, {'value': 'bad'}, type_vars={FutureT: int})

            with self.assertRaises(TypeError):
                load(FutureListBox[int], {'items': [1, 'bad']})

            with self.assertRaises(TypeError):
                load(FutureOptionalBox[int], {'maybe': 'bad'})

            with self.assertRaises(ValidationError) as cm:
                validate(FutureOptionalBox[int], {'maybe': 'bad'},
                         collect_errors=True)
            self.assertEqual([issue.path for issue in cm.exception.errors],
                             ['maybe'])
        finally:
            for name, value in previous.items():
                if value is sentinel:
                    globals().pop(name, None)
                else:
                    globals()[name] = value

    def test_future_annotations_preserve_pep604_type_vars(self):
        if sys.version_info < (3, 10):
            self.skipTest('PEP 604 annotations require Python 3.10+')

        sentinel = object()
        names = ('FuturePipeT', 'FuturePipeBox')
        previous = dict((name, globals().get(name, sentinel)) for name in names)
        try:
            six.exec_(
                'from __future__ import annotations\n'
                'FuturePipeT = TypeVar("FuturePipeT")\n'
                '@dataclass\n'
                'class FuturePipeBox(Generic[FuturePipeT]):\n'
                '    maybe: FuturePipeT | None\n'
                '    either: FuturePipeT | str\n',
                globals())
            FuturePipeBox = globals()['FuturePipeBox']

            obj = load(FuturePipeBox[int], {'maybe': None, 'either': 42})
            str_union_obj = load(
                FuturePipeBox[int], {'maybe': 7, 'either': 'ok'})

            self.assertIsNone(obj.maybe)
            self.assertEqual(obj.either, 42)
            self.assertEqual(str_union_obj.maybe, 7)
            self.assertEqual(str_union_obj.either, 'ok')

            with self.assertRaises(TypeError):
                load(FuturePipeBox[int], {'maybe': 'bad', 'either': 42})

            with self.assertRaises(TypeError):
                load(FuturePipeBox[int], {'maybe': 1, 'either': 1.5})

            with self.assertRaises(ValidationError) as cm:
                validate(FuturePipeBox[int],
                         {'maybe': 'bad', 'either': 1.5},
                         collect_errors=True)
            self.assertEqual([issue.path for issue in cm.exception.errors],
                             ['maybe', 'either'])
        finally:
            for name, value in previous.items():
                if value is sentinel:
                    globals().pop(name, None)
                else:
                    globals()[name] = value

    def test_future_annotations_preserve_nested_generic_type_vars(self):
        if sys.version_info < (3,):
            self.skipTest('future annotations are Python 3 only')

        sentinel = object()
        names = ('FutureNestedT', 'FutureInner', 'FutureOuter')
        previous = dict((name, globals().get(name, sentinel)) for name in names)
        try:
            six.exec_(
                'from __future__ import annotations\n'
                'FutureNestedT = TypeVar("FutureNestedT")\n'
                '@dataclass\n'
                'class FutureInner(Generic[FutureNestedT]):\n'
                '    value: FutureNestedT\n'
                '@dataclass\n'
                'class FutureOuter(Generic[FutureNestedT]):\n'
                '    inner: FutureInner[FutureNestedT]\n'
                '    mapping: Dict[str, FutureInner[FutureNestedT]]\n',
                globals())
            FutureInner = globals()['FutureInner']
            FutureOuter = globals()['FutureOuter']

            obj = load(FutureOuter[int], {
                'inner': {'value': 1},
                'mapping': {'a': {'value': 2}},
            })

            self.assertIsInstance(obj.inner, FutureInner)
            self.assertIsInstance(obj.mapping['a'], FutureInner)
            self.assertEqual(obj.inner.value, 1)
            self.assertEqual(obj.mapping['a'].value, 2)

            with self.assertRaises(TypeError):
                load(FutureOuter[int], {
                    'inner': {'value': 'bad'},
                    'mapping': {'a': {'value': 2}},
                })

            with self.assertRaises(TypeError):
                load(FutureOuter[int], {
                    'inner': {'value': 1},
                    'mapping': {'a': {'value': 'bad'}},
                })

            with self.assertRaises(ValidationError) as cm:
                validate(FutureOuter[int], {
                    'inner': {'value': 'bad'},
                    'mapping': {'a': {'value': 'bad'}},
                }, collect_errors=True)
            self.assertEqual([issue.path for issue in cm.exception.errors],
                             ['inner.value', 'mapping[a].value'])
        finally:
            for name, value in previous.items():
                if value is sentinel:
                    globals().pop(name, None)
                else:
                    globals()[name] = value

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

    def test_generic_alias_inside_generic_field(self):
        data = {
            'box': {'value': 1},
            'boxes': [{'value': 2}, {'value': 3}],
            'mapping': {'a': {'value': 4}},
        }

        obj = load(GenericAliasFields[int], data)

        self.assertEqual(obj.box.value, 1)
        self.assertEqual([box.value for box in obj.boxes], [2, 3])
        self.assertEqual(obj.mapping['a'].value, 4)
        self.assertIsInstance(obj.box, Box)
        self.assertIsInstance(obj.boxes[0], Box)
        self.assertIsInstance(obj.mapping['a'], Box)

    def test_generic_alias_inside_generic_field_rejects(self):
        data = {
            'box': {'value': 'bad'},
            'boxes': [{'value': 1}, {'value': 'bad'}],
            'mapping': {'a': {'value': 'bad'}},
        }

        with self.assertRaises(ValidationError) as cm:
            validate(GenericAliasFields[int], data, collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['box.value', 'boxes[1].value',
                          'mapping[a].value'])

    def test_generic_optional_union_fields(self):
        none_data = {'maybe': None, 'either': 1}
        str_union_data = {'maybe': 2, 'either': 'ok'}

        none_obj = load(GenericOptionalUnion[int], none_data)
        str_union_obj = load(GenericOptionalUnion[int], str_union_data)

        self.assertIsNone(none_obj.maybe)
        self.assertEqual(none_obj.either, 1)
        self.assertEqual(str_union_obj.maybe, 2)
        self.assertEqual(str_union_obj.either, 'ok')

    def test_generic_optional_union_fields_rejects(self):
        data = {'maybe': 'bad', 'either': 1.5}

        with self.assertRaises(ValidationError) as cm:
            validate(GenericOptionalUnion[int], data, collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['maybe', 'either'])

    def test_string_generic_annotations_resolve(self):
        data = {
            'item': 1,
            'maybe': None,
            'box': {'value': 2},
            'boxes': [{'value': 3}],
        }

        obj = load(StringGenericAnnotations[int], data)

        self.assertEqual(obj.item, 1)
        self.assertIsNone(obj.maybe)
        self.assertEqual(obj.box.value, 2)
        self.assertEqual(obj.boxes[0].value, 3)

    def test_string_generic_annotations_reject(self):
        data = {
            'item': 'bad',
            'maybe': 'bad',
            'box': {'value': 'bad'},
            'boxes': [{'value': 'bad'}],
        }

        with self.assertRaises(ValidationError) as cm:
            validate(StringGenericAnnotations[int], data, collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['item', 'maybe', 'box.value', 'boxes[0].value'])

    # --- T resolved to a dataclass ---

    def test_typevar_resolved_to_dataclass(self):
        obj = load(Box, {'value': {'name': 'Alice', 'age': 30}}, type_vars={T: User})
        self.assertIsInstance(obj.value, User)
        self.assertEqual(obj.value.name, 'Alice')

    def test_typevar_resolved_in_nested_dataclass(self):
        obj = load(GenericNested, {'name': 'nested', 'box': {'value': 42}},
                   type_vars={T: int})
        self.assertEqual(obj.box.value, 42)

    def test_typevar_resolved_in_nested_dataclass_rejects(self):
        with self.assertRaises(TypeError):
            load(GenericNested, {'name': 'nested', 'box': {'value': 'bad'}},
                 type_vars={T: int})

    def test_parameterized_nested_dataclass_field(self):
        obj = load(WithParameterizedBox, {'box': {'value': 42}})

        self.assertIsInstance(obj.box, Box)
        self.assertEqual(obj.box.value, 42)

    def test_parameterized_nested_dataclass_field_rejects(self):
        with self.assertRaises(TypeError) as cm:
            load(WithParameterizedBox, {'box': {'value': 'bad'}})

        msg = str(cm.exception)
        self.assertIn('box.value', msg)
        self.assertIn('int', msg)

    def test_parameterized_nested_dataclass_list_field(self):
        obj = load(WithParameterizedBoxList,
                   {'boxes': [{'value': 1}, {'value': 2}]})

        self.assertEqual([box.value for box in obj.boxes], [1, 2])
        self.assertIsInstance(obj.boxes[0], Box)

    def test_parameterized_nested_dataclass_list_field_rejects(self):
        with self.assertRaises(TypeError) as cm:
            load(WithParameterizedBoxList,
                 {'boxes': [{'value': 1}, {'value': 'bad'}]})

        msg = str(cm.exception)
        self.assertIn('boxes[1].value', msg)
        self.assertIn('int', msg)

    def test_parameterized_nested_dataclass_dict_field(self):
        obj = load(WithParameterizedBoxDict,
                   {'boxes': {'first': {'value': 1}, 'second': {'value': 2}}})

        self.assertEqual(obj.boxes['first'].value, 1)
        self.assertEqual(obj.boxes['second'].value, 2)

    def test_parameterized_nested_dataclass_dict_field_rejects(self):
        with self.assertRaises(TypeError) as cm:
            load(WithParameterizedBoxDict,
                 {'boxes': {'first': {'value': 1}, 'bad': {'value': 'bad'}}})

        msg = str(cm.exception)
        self.assertIn('boxes[bad].value', msg)
        self.assertIn('int', msg)

    def test_parameterized_nested_dataclass_field_resolved_to_dataclass(self):
        obj = load(WithParameterizedUserBox,
                   {'box': {'value': {'name': 'Alice', 'age': 30}}})

        self.assertIsInstance(obj.box.value, User)
        self.assertEqual(obj.box.value.name, 'Alice')

    def test_parameterized_nested_dataclass_field_resolved_to_dataclass_rejects(self):
        with self.assertRaises(TypeError) as cm:
            load(WithParameterizedUserBox,
                 {'box': {'value': {'name': 'Alice', 'age': 'bad'}}})

        msg = str(cm.exception)
        self.assertIn('box.value.age', msg)
        self.assertIn('int', msg)

    def test_list_typevar_resolved_to_dataclass(self):
        data = {'items': [{'name': 'Alice', 'age': 30}, {'name': 'Bob', 'age': 25}]}
        obj = load(GenericList, data, type_vars={T: User})
        self.assertEqual(len(obj.items), 2)
        self.assertIsInstance(obj.items[0], User)

    # --- Classmethod with type_vars ---

    def test_generic_classmethod_requires_type_vars(self):
        with self.assertRaises(TypeError):
            Box.load({'value': 42})

        with self.assertRaises(TypeError):
            Box.load({'value': 42}, type_vars={})

        with self.assertRaises(TypeError):
            Box.loads('{"value": 42}')

        with self.assertRaises(TypeError):
            Box.loads('{"value": 42}', type_vars={})

        with self.assertRaises(TypeError):
            Box[int].load({'value': 42})

        with self.assertRaises(TypeError):
            Box[int].loads('{"value": 42}')

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
        with self.assertRaises(TypeError) as cm:
            load(Box, {'value': 'bad'}, type_vars={T: int})

        msg = str(cm.exception)
        self.assertIn('value', msg)
        self.assertIn('int', msg)

    def test_list_typevar_error_path(self):
        with self.assertRaises(TypeError) as cm:
            load(GenericList, {'items': [1, 'bad']}, type_vars={T: int})

        self.assertIn('items[1]', str(cm.exception))


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

    def test_inherited_generic_transform_accepts(self):
        obj = load(IntListBoxWithOwn, {'value': [1, 2], 'item': 3})
        alias_obj = load(ListBoxWithOwn[int], {'value': [4, 5], 'item': 6})

        self.assertEqual(obj.value, [1, 2])
        self.assertEqual(obj.item, 3)
        self.assertEqual(alias_obj.value, [4, 5])
        self.assertEqual(alias_obj.item, 6)

    def test_inherited_generic_transform_with_explicit_type_vars(self):
        obj = load(ListBoxWithOwn, {'value': [1, 2], 'item': 3},
                   type_vars={T: int})

        self.assertEqual(obj.value, [1, 2])
        self.assertEqual(obj.item, 3)

        with self.assertRaises(ValidationError) as cm:
            validate(ListBoxWithOwn, {'value': [1, 'bad'], 'item': 'bad'},
                     type_vars={T: int}, collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['value[1]', 'item'])

    def test_inherited_generic_transform_rejects_base_field_element(self):
        with self.assertRaises(TypeError) as cm:
            load(IntListBoxWithOwn, {'value': [1, 'bad'], 'item': 3})

        self.assertIn('value[1]', str(cm.exception))

    def test_inherited_generic_transform_rejects_owner_field(self):
        with self.assertRaises(TypeError) as cm:
            load(IntListBoxWithOwn, {'value': [1, 2], 'item': 'bad'})

        self.assertIn('item', str(cm.exception))

    def test_inherited_generic_transform_collects_errors(self):
        with self.assertRaises(ValidationError) as cm:
            validate(IntListBoxWithOwn, {'value': [1, 'bad'], 'item': 'bad'},
                     collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['value[1]', 'item'])

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

    def test_inherited_generic_reordered_type_vars_accepts(self):
        obj = load(SwappedIntStrPair, {'first': 'hello', 'second': 42})
        alias_obj = load(SwappedPair[int, str],
                         {'first': 'world', 'second': 7})

        self.assertEqual(obj.first, 'hello')
        self.assertEqual(obj.second, 42)
        self.assertEqual(alias_obj.first, 'world')
        self.assertEqual(alias_obj.second, 7)

    def test_inherited_generic_reordered_type_vars_rejects(self):
        with self.assertRaises(ValidationError) as cm:
            validate(SwappedIntStrPair, {'first': 1, 'second': 'bad'},
                     collect_errors=True)

        self.assertEqual([issue.path for issue in cm.exception.errors],
                         ['first', 'second'])

    def test_future_annotations_inherited_generic_transform(self):
        if sys.version_info < (3,):
            self.skipTest('future annotations are Python 3 only')

        sentinel = object()
        names = ('FutureInheritedT', 'FutureInheritedBase',
                 'FutureInheritedListBase', 'FutureInheritedIntList')
        previous = dict((name, globals().get(name, sentinel)) for name in names)
        try:
            six.exec_(
                'from __future__ import annotations\n'
                'FutureInheritedT = TypeVar("FutureInheritedT")\n'
                '@dataclass\n'
                'class FutureInheritedBase(Generic[FutureInheritedT]):\n'
                '    value: FutureInheritedT\n'
                '@dataclass\n'
                'class FutureInheritedListBase('
                'FutureInheritedBase[List[FutureInheritedT]], '
                'Generic[FutureInheritedT]):\n'
                '    item: FutureInheritedT\n'
                '@dataclass\n'
                'class FutureInheritedIntList('
                'FutureInheritedListBase[int]):\n'
                '    pass\n',
                globals())
            FutureInheritedIntList = globals()['FutureInheritedIntList']

            obj = load(FutureInheritedIntList, {
                'value': [1, 2],
                'item': 3,
            })

            self.assertEqual(obj.value, [1, 2])
            self.assertEqual(obj.item, 3)

            with self.assertRaises(ValidationError) as cm:
                validate(FutureInheritedIntList, {
                    'value': [1, 'bad'],
                    'item': 'bad',
                }, collect_errors=True)

            self.assertEqual([issue.path for issue in cm.exception.errors],
                             ['value[1]', 'item'])
        finally:
            for name, value in previous.items():
                if value is sentinel:
                    globals().pop(name, None)
                else:
                    globals()[name] = value

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
        with self.assertRaises(TypeError) as cm:
            load(ConstrainedBox, {'value': 3.14})

        msg = str(cm.exception)
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

    def test_dumps_and_generated_dump_delegate_to_dump(self):
        import _py2dataclasses.dataclasses as impl

        original_dump = impl.dump
        calls = []
        p = Point(7, 8)

        def marker_factory(pairs):
            return dict(pairs)

        def fake_dump(obj, dict_factory=impl._default_dict_factory):
            calls.append((obj, dict_factory))
            return {'sentinel': 1}

        try:
            impl.dump = fake_dump
            generated_dump_result = p.dump()
            module_dumps_result = json.loads(dumps(p))
            generated_dumps_result = json.loads(p.dumps())
            module_dumps_with_factory = json.loads(
                dumps(p, dict_factory=marker_factory))
            generated_dumps_with_factory = json.loads(
                p.dumps(dict_factory=marker_factory))
        finally:
            impl.dump = original_dump

        self.assertEqual(generated_dump_result, {'sentinel': 1})
        self.assertEqual(module_dumps_result, {'sentinel': 1})
        self.assertEqual(generated_dumps_result, {'sentinel': 1})
        self.assertEqual(module_dumps_with_factory, {'sentinel': 1})
        self.assertEqual(generated_dumps_with_factory, {'sentinel': 1})
        self.assertEqual([call[0] for call in calls], [p, p, p, p, p])
        self.assertIs(calls[3][1], marker_factory)
        self.assertIs(calls[4][1], marker_factory)

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

    def test_dumps_accepts_custom_serializer(self):
        _BytesSerializer.dump_kwargs = None

        payload = dumps(Point(1, 2), serializer=_BytesSerializer,
                        use_bin_type=True)
        data = _BytesSerializer.loads(payload)

        self.assertTrue(payload.startswith(b'packed:'))
        self.assertEqual(data, {'x': 1, 'y': 2})
        self.assertEqual(_BytesSerializer.dump_kwargs,
                         {'use_bin_type': True})

    def test_dump_nested(self):
        obj = UserWithAddress('John', Address('NYC', '10001'))
        d = dump(obj)
        self.assertEqual(d['address']['city'], 'NYC')

    def test_generated_method_names_do_not_override_fields(self):
        @dataclass
        class WithGeneratedMethodNameFields(object):
            load = field(int)
            loads = field(str)
            dump = field(int)
            dumps = field(str)

        data = {
            'load': 1,
            'loads': 'from-json',
            'dump': 2,
            'dumps': 'to-json',
        }

        obj = load(WithGeneratedMethodNameFields, data)
        dumped = dump(obj)

        self.assertEqual(obj.load, 1)
        self.assertEqual(obj.loads, 'from-json')
        self.assertEqual(obj.dump, 2)
        self.assertEqual(obj.dumps, 'to-json')
        self.assertFalse(callable(getattr(WithGeneratedMethodNameFields, 'load', None)))
        self.assertFalse(callable(getattr(WithGeneratedMethodNameFields, 'loads', None)))
        self.assertFalse(callable(getattr(WithGeneratedMethodNameFields, 'dump', None)))
        self.assertFalse(callable(getattr(WithGeneratedMethodNameFields, 'dumps', None)))
        self.assertEqual(dumped, {
            'load': 1,
            'loads': 'from-json',
            'dump': 2,
            'dumps': 'to-json',
        })

    def test_inherited_generated_method_names_do_not_override_fields(self):
        @dataclass
        class GeneratedMethodBase(object):
            x = field(int)

        @dataclass
        class GeneratedMethodChild(GeneratedMethodBase):
            load = field(int)
            loads = field(str)
            dump = field(int)
            dumps = field(str)

        base = GeneratedMethodBase.load({'x': 1})
        base_loaded = GeneratedMethodBase.loads('{"x": 2}')
        base_dumped = GeneratedMethodBase(3).dump()
        base_dumps_parsed = json.loads(GeneratedMethodBase(4).dumps())
        child_has_generated_names = [
            hasattr(GeneratedMethodChild, name)
            for name in ('load', 'loads', 'dump', 'dumps')
        ]
        child_data = {
            'x': 5,
            'load': 6,
            'loads': 'from-json',
            'dump': 7,
            'dumps': 'to-json',
        }
        obj = load(GeneratedMethodChild, child_data)
        dumped = dump(obj)

        self.assertEqual(base.x, 1)
        self.assertEqual(base_loaded.x, 2)
        self.assertEqual(base_dumped, {'x': 3})
        self.assertEqual(base_dumps_parsed['x'], 4)
        self.assertEqual(child_has_generated_names,
                         [False, False, False, False])
        self.assertEqual(obj.load, 6)
        self.assertEqual(obj.loads, 'from-json')
        self.assertEqual(obj.dump, 7)
        self.assertEqual(obj.dumps, 'to-json')
        self.assertEqual(dumped, {
            'x': 5,
            'load': 6,
            'loads': 'from-json',
            'dump': 7,
            'dumps': 'to-json',
        })

    def test_inherited_user_methods_are_not_overridden(self):
        @dataclass
        class UserMethodBase(object):
            x = field(int)

            @classmethod
            def load(cls, data):
                return 'custom-load:{0}'.format(cls.__name__)

            @classmethod
            def loads(cls, payload):
                return 'custom-loads:{0}'.format(cls.__name__)

            def dump(self):
                return {'custom': self.x}

            def dumps(self):
                return 'custom-dumps:{0}'.format(self.x)

        @dataclass
        class UserMethodChild(UserMethodBase):
            y = field(int)

        obj = UserMethodChild(1, 2)
        base_load = UserMethodBase.load({})
        child_load = UserMethodChild.load({})
        child_loads = UserMethodChild.loads('{}')
        dumped = obj.dump()
        dumped_payload = obj.dumps()

        self.assertEqual(base_load, 'custom-load:UserMethodBase')
        self.assertEqual(child_load, 'custom-load:UserMethodChild')
        self.assertEqual(child_loads, 'custom-loads:UserMethodChild')
        self.assertEqual(dumped, {'custom': 1})
        self.assertEqual(dumped_payload, 'custom-dumps:1')


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

    def test_roundtrip_loads_dumps_custom_serializer_classmethods(self):
        p = Point(42, 99)
        payload = p.dumps(serializer=_BytesSerializer, use_bin_type=True)
        p2 = Point.loads(payload, serializer=_BytesSerializer, raw=False)
        self.assertEqual(p, p2)
        self.assertEqual(_BytesSerializer.dump_kwargs,
                         {'use_bin_type': True})
        self.assertEqual(_BytesSerializer.load_kwargs, {'raw': False})

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

        with self.assertRaises(TypeError) as cm:
            load(UserWithAddress, data)

        msg = str(cm.exception)
        self.assertIn('address.city', msg)
        self.assertIn('str', msg)

    def test_list_element_error_path(self):
        with self.assertRaises(TypeError) as cm:
            load(WithList, {'values': [1, 'bad', 3]})

        self.assertIn('values[1]', str(cm.exception))

    def test_missing_field_error(self):
        with self.assertRaises(ValueError) as cm:
            load(Point, {'x': 1})

        msg = str(cm.exception)
        self.assertIn('y', msg)
        self.assertIn('Point', msg)


if __name__ == '__main__':
    unittest.main()
