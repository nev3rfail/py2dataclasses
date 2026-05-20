from __future__ import print_function
from tests.load_fixtures import *

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

        def fake_load(cls, data, unknown=RAISE, strict_types=False,
                      type_vars=None, collect_errors=False):
            calls.append((cls, data, unknown, strict_types, type_vars,
                          collect_errors))
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

    def test_load_extra_keys_raise_by_default(self):
        with self.assertRaises(TypeError):
            load(Point, {'x': 1, 'y': 2, 'z': 3})

    def test_load_extra_keys_excluded(self):
        p = load(Point, {'x': 1, 'y': 2, 'z': 3}, unknown=EXCLUDE)
        self.assertEqual(p.x, 1)
        self.assertEqual(p.y, 2)

    def test_load_extra_keys_unknown_raise(self):
        with self.assertRaises(TypeError):
            load(Point, {'x': 1, 'y': 2, 'z': 3}, unknown=RAISE)

    def test_load_non_string_extra_key_reports_unknown_field(self):
        with self.assertRaises(TypeError) as cm:
            load(Point, {'x': 1, 'y': 2, 1: 'extra'}, unknown=RAISE)

        self.assertIn('Unknown fields for Point: 1', str(cm.exception))

    def test_load_nested_extra_keys_raise_by_default(self):
        with self.assertRaises(TypeError):
            load(UserWithAddress,
                 {'name': 'John',
                  'address': {'city': 'NYC', 'zip_code': '10001',
                              'extra': True}})

    def test_load_nested_extra_keys_excluded(self):
        obj = load(UserWithAddress,
                   {'name': 'John',
                    'address': {'city': 'NYC', 'zip_code': '10001',
                                'extra': True}},
                   unknown=EXCLUDE)

        self.assertEqual(obj.address.city, 'NYC')


class TestLoadPlanCache(unittest.TestCase):

    def _clear_plan_cache(self, cls):
        import _py2dataclasses.dataclasses as impl
        try:
            delattr(cls, impl._LOAD_FIELD_PLAN_CACHE)
        except AttributeError:
            pass
        return impl

    def test_load_plan_cache_covers_common_shapes(self):
        import _py2dataclasses.dataclasses as impl

        @dataclass
        class PlanInner(object):
            value = field(int)

        @dataclass
        class PlanShape(object):
            scalar = field(int)
            optional = field(Optional[int])
            any_value = field(Any)
            nested = field(PlanInner)
            values = field(List[int])
            mapping = field(Dict[str, int])
            pair = field(Tuple[int, str])
            value_set = field(Set[int])

        payload = {
            'scalar': '1',
            'optional': '2',
            'any_value': object(),
            'nested': {'value': '3'},
            'values': ['4', 5],
            'mapping': {'a': '6'},
            'pair': ['7', 'seven'],
            'value_set': ['8', 9],
        }

        obj = load(PlanShape, payload)
        self.assertEqual(obj.scalar, 1)
        self.assertEqual(obj.optional, 2)
        self.assertIsInstance(obj.nested, PlanInner)
        self.assertEqual(obj.values, [4, 5])
        self.assertEqual(obj.mapping, {'a': 6})
        self.assertEqual(obj.pair, (7, 'seven'))
        self.assertEqual(obj.value_set, set([8, 9]))

        cache = getattr(PlanShape, impl._LOAD_FIELD_PLAN_CACHE)
        self.assertEqual(
            sorted(cache.keys()),
            ['any_value', 'mapping', 'nested', 'optional', 'pair',
             'scalar', 'value_set', 'values'])
        first_plans = dict(cache)

        load(PlanShape, payload)
        for name, plan in first_plans.items():
            self.assertIs(cache[name], plan)

    def test_load_plan_cache_is_per_class_for_same_field_name(self):
        import _py2dataclasses.dataclasses as impl

        @dataclass
        class IntValue(object):
            value = field(int)

        @dataclass
        class StrValue(object):
            value = field(str)

        int_obj = load(IntValue, {'value': '10'})
        str_obj = load(StrValue, {'value': '10'})

        self.assertEqual(int_obj.value, 10)
        self.assertEqual(str_obj.value, '10')
        self.assertIsNot(
            getattr(IntValue, impl._LOAD_FIELD_PLAN_CACHE),
            getattr(StrValue, impl._LOAD_FIELD_PLAN_CACHE))

    def test_explicit_type_vars_skip_load_plan_cache(self):
        impl = self._clear_plan_cache(Box)

        obj = load(Box, {'value': '10'}, type_vars={T: int})

        self.assertEqual(obj.value, 10)
        self.assertFalse(hasattr(Box, impl._LOAD_FIELD_PLAN_CACHE))

    def test_collect_errors_does_not_use_load_plan_cache(self):
        impl = self._clear_plan_cache(WithList)

        obj = load(WithList, {'values': ['1', 2]}, collect_errors=True)

        self.assertEqual(obj.values, [1, 2])
        self.assertFalse(hasattr(WithList, impl._LOAD_FIELD_PLAN_CACHE))

    def test_validate_and_load_share_class_plan_cache(self):
        import _py2dataclasses.dataclasses as impl

        @dataclass
        class ClassPlanShape(object):
            values = field(List[int])

        validate(ClassPlanShape, {'values': ['1', 2]})

        class_plan = getattr(ClassPlanShape, impl._LOAD_CLASS_PLAN_CACHE)
        known_names, loadable_fields, ordered_entries = class_plan
        self.assertEqual(known_names, frozenset(['values']))
        self.assertEqual([f.name for f in loadable_fields], ['values'])
        self.assertIsNone(ordered_entries)

        load(ClassPlanShape, {'values': ['3', 4]})
        self.assertIs(
            getattr(ClassPlanShape, impl._LOAD_CLASS_PLAN_CACHE),
            class_plan)

    def test_class_plan_preserves_classvar_error(self):
        import _py2dataclasses.dataclasses as impl

        try:
            delattr(WithClassVar, impl._LOAD_CLASS_PLAN_CACHE)
        except AttributeError:
            pass

        with self.assertRaises(TypeError) as cm:
            load(WithClassVar, {'x': 1, 'class_val': 2, 'extra': 3})

        self.assertIn('is ClassVar and cannot be loaded', str(cm.exception))
        known_names, loadable_fields, ordered_entries = getattr(
            WithClassVar, impl._LOAD_CLASS_PLAN_CACHE)
        self.assertEqual(known_names, frozenset(['class_val', 'x']))
        self.assertEqual([f.name for f in loadable_fields], ['x'])
        self.assertIsNotNone(ordered_entries)


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

    def test_int_coerces_numeric_string(self):
        obj = load(Point, {'x': '42', 'y': 2})

        self.assertEqual(obj.x, 42)

    def test_int_string_rejected_with_strict_types(self):
        with self.assertRaises(TypeError):
            load(Point, {'x': '42', 'y': 2}, strict_types=True)

    def test_int_to_float_coercion(self):
        obj = load(WithFloat, {'value': 42})
        self.assertIsInstance(obj.value, float)
        self.assertEqual(obj.value, 42.0)

    def test_float_coerces_numeric_string(self):
        obj = load(WithFloat, {'value': '3.14'})

        self.assertEqual(obj.value, 3.14)

    def test_float_stays_float(self):
        obj = load(WithFloat, {'value': 3.14})
        self.assertEqual(obj.value, 3.14)

    def test_float_int_rejected_with_strict_types(self):
        with self.assertRaises(TypeError):
            load(WithFloat, {'value': 42}, strict_types=True)

    def test_float_string_rejected_with_strict_types(self):
        with self.assertRaises(TypeError):
            load(WithFloat, {'value': '3.14'}, strict_types=True)

    def test_bool_not_accepted_as_float(self):
        with self.assertRaises(TypeError):
            load(WithFloat, {'value': True})

    def test_bool_valid(self):
        obj = load(WithBool, {'flag': True})
        self.assertTrue(obj.flag)

    def test_bool_coerces_truthy_and_falsy_values(self):
        truthy_values = ['true', 'True', '1', 1]
        falsy_values = ['false', 'False', '0', 0]

        for value in truthy_values:
            self.assertIs(load(WithBool, {'flag': value}).flag, True)
        for value in falsy_values:
            self.assertIs(load(WithBool, {'flag': value}).flag, False)

    def test_bool_rejects_unknown_string(self):
        with self.assertRaises(TypeError):
            load(WithBool, {'flag': 'maybe'})

    def test_bool_string_rejected_with_strict_types(self):
        with self.assertRaises(TypeError):
            load(WithBool, {'flag': 'true'}, strict_types=True)

    def test_bool_int_rejected_with_strict_types(self):
        with self.assertRaises(TypeError):
            load(WithBool, {'flag': 1}, strict_types=True)

    def test_str_decodes_bytes_on_python3(self):
        if sys.version_info < (3,):
            self.skipTest('bytes are str on Python 2')

        obj = load(User, {'name': b'Alice', 'age': 25})

        self.assertEqual(obj.name, 'Alice')

    def test_str_bytes_rejected_with_strict_types_on_python3(self):
        if sys.version_info < (3,):
            self.skipTest('bytes are str on Python 2')

        with self.assertRaises(TypeError):
            load(User, {'name': b'Alice', 'age': 25}, strict_types=True)

    def test_recursive_coercion_respects_strict_types(self):
        obj = load(WithList, {'values': ['1', '2']})

        self.assertEqual(obj.values, [1, 2])

        with self.assertRaises(TypeError):
            load(WithList, {'values': ['1', '2']}, strict_types=True)

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

    def test_unresolved_field_type_is_error(self):
        data = {'value': 42}

        with self.assertRaises(TypeError) as cm:
            load(WithUnresolvedType, data)

        self.assertIn('value', str(cm.exception))
        self.assertIn('unsupported type annotation', str(cm.exception))

        with self.assertRaises(ValidationError) as collect_cm:
            validate(WithUnresolvedType, data, collect_errors=True)
        self.assertEqual([issue.path for issue in collect_cm.exception.errors],
                         ['value'])
        self.assertIn('unsupported type annotation',
                      collect_cm.exception.errors[0].message)

    def test_unsupported_generic_field_type_is_error(self):
        data = {'callback': lambda value: str(value)}

        with self.assertRaises(TypeError) as cm:
            load(WithCallableType, data)

        self.assertIn('callback', str(cm.exception))
        self.assertIn('unsupported type annotation', str(cm.exception))

        with self.assertRaises(ValidationError) as collect_cm:
            validate(WithCallableType, data, collect_errors=True)
        self.assertEqual([issue.path for issue in collect_cm.exception.errors],
                         ['callback'])
        self.assertIn('unsupported type annotation',
                      collect_cm.exception.errors[0].message)

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

if __name__ == '__main__':
    unittest.main()
