from __future__ import print_function
from tests.load_fixtures import *

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
            lambda: load(User, data, unknown=RAISE, collect_errors=True),
            ['name', 'age', 'extra'])

        self.assertEqual(exc.errors[0].path, 'name')
        self.assertIn('expected str', exc.errors[0].message)

    def test_validate_collects_missing_type_and_unknown_errors(self):
        data = {'x': 'bad', 'z': 3}

        exc = self.assertValidationPaths(
            lambda: validate(Point, data, unknown=RAISE,
                             collect_errors=True),
            ['x', 'y', 'z'])

        messages = dict((issue.path, issue.message) for issue in exc.errors)
        self.assertIn('expected int', messages['x'])
        self.assertIn('missing required field', messages['y'])
        self.assertIn('unknown field', messages['z'])

    def test_collect_errors_handles_non_string_unknown_keys(self):
        exc = self.assertValidationPaths(
            lambda: validate(Point, {'x': 1, 'y': 2, 1: 'extra'},
                             unknown=RAISE, collect_errors=True),
            ['1'])

        self.assertIn('unknown field', exc.errors[0].message)

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

    def test_collect_errors_nested_unknown_paths(self):
        data = {
            'name': 'John',
            'address': {
                'city': 'NYC',
                'zip_code': '10001',
                'extra': True,
            },
        }

        self.assertValidationPaths(
            lambda: load(UserWithAddress, data, unknown=RAISE,
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
            load(ConstrainedBox, {'value': []}, type_vars={CT: CT},
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

    def test_collect_errors_init_false_unknown_path(self):
        with self.assertRaises(ValidationError) as init_false:
            load(WithInitFalse, {'x': 1, 'y': 2}, unknown=RAISE,
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

if __name__ == '__main__':
    unittest.main()
