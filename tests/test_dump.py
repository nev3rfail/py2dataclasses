from __future__ import print_function
from tests.load_fixtures import *

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

    def test_dump_ordered_dict_factory_preserves_order(self):
        from collections import OrderedDict

        @dataclass
        class OrderedDumpInner(object):
            left = field(int)
            right = field(int)

        @dataclass
        class OrderedDumpOuter(object):
            name = field(str)
            count = field(int)
            inner = field(OrderedDumpInner)

        d = dump(OrderedDumpOuter('outer', 2, OrderedDumpInner(3, 4)),
                 dict_factory=OrderedDict)

        self.assertIs(type(d), OrderedDict)
        self.assertIs(type(d['inner']), OrderedDict)
        self.assertEqual(list(d.keys()), ['name', 'count', 'inner'])
        self.assertEqual(list(d['inner'].keys()), ['left', 'right'])

    def test_dump_custom_dict_factory_still_receives_pairs(self):
        calls = []

        def recording_factory(pairs):
            calls.append(pairs)
            return dict(pairs)

        d = dump(Point(1, 2), dict_factory=recording_factory)

        self.assertEqual(d, {'x': 1, 'y': 2})
        self.assertEqual(calls, [[('x', 1), ('y', 2)]])

    def test_fields_cache_is_per_class(self):
        import _py2dataclasses.dataclasses as impl

        @dataclass
        class DumpFieldsBase(object):
            x = field(int)

        @dataclass
        class DumpFieldsChild(DumpFieldsBase):
            y = field(int)

        base_fields = impl.fields(DumpFieldsBase)
        child_fields = impl.fields(DumpFieldsChild)

        self.assertIs(impl.fields(DumpFieldsBase), base_fields)
        self.assertIs(impl.fields(DumpFieldsChild(1, 2)), child_fields)
        self.assertEqual([f.name for f in base_fields], ['x'])
        self.assertEqual([f.name for f in child_fields], ['x', 'y'])
        self.assertIsNot(
            getattr(DumpFieldsBase, impl._FIELDS_CACHE),
            getattr(DumpFieldsChild, impl._FIELDS_CACHE))

    def test_cache_false_disables_fields_cache(self):
        import _py2dataclasses.dataclasses as impl

        @dataclass(cache=False)
        class DumpNoCache(object):
            x = field(int)

        first_fields = impl.fields(DumpNoCache)
        second_fields = impl.fields(DumpNoCache)
        dumped = dump(DumpNoCache(1))

        self.assertFalse(DumpNoCache.__dataclass_params__.cache)
        self.assertIsNot(first_fields, second_fields)
        self.assertEqual([f.name for f in first_fields], ['x'])
        self.assertEqual(dumped, {'x': 1})
        self.assertFalse(hasattr(DumpNoCache, impl._FIELDS_CACHE))

    def test_make_dataclass_accepts_cache_false(self):
        import _py2dataclasses.dataclasses as impl

        MadeNoCache = impl.make_dataclass(
            'MadeNoCache', [('x', int)], cache=False)

        self.assertFalse(MadeNoCache.__dataclass_params__.cache)
        self.assertEqual(impl.fields(MadeNoCache)[0].name, 'x')
        self.assertFalse(hasattr(MadeNoCache, impl._FIELDS_CACHE))

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
