from load_test import *

class TestMakeDataclass(unittest.TestCase):
    def test_simple(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', int, field(int, default=5))],
                           namespace={'add_one': lambda self: self.x + 1})
        c = C(10)
        self.assertEqual((c.x, c.y), (10, 5))
        self.assertEqual(c.add_one(), 11)

    def test_no_mutate_namespace(self):
        # Make sure a provided namespace isn't mutated.
        ns = {}
        C = make_dataclass('C',
                           [('x', int),
                            ('y', int, field(int, default=5))],
                           namespace=ns)
        self.assertEqual(ns, {})

    def test_base(self):
        class Base1(object):
            pass
        class Base2(object):
            pass
        C = make_dataclass('C',
                           [('x', int)],
                           bases=(Base1, Base2))
        c = C(2)
        self.assertIsInstance(c, C)
        self.assertIsInstance(c, Base1)
        self.assertIsInstance(c, Base2)

    def test_base_dataclass(self):
        @dataclass
        class Base1(object):
            #__annotations__ = {'x': int}
            x = field(int)

        class Base2(object):
            pass

        C = make_dataclass('C',
                           [('y', int)],
                           bases=(Base1, Base2))
        with self.assertRaisesRegexp(TypeError, '__init__\(\) takes exactly 3 arguments \(2 given\)'):
            c = C(2)
        c = C(1, 2)
        self.assertIsInstance(c, C)
        self.assertIsInstance(c, Base1)
        self.assertIsInstance(c, Base2)

        self.assertEqual((c.x, c.y), (1, 2))

    def test_no_types(self):
        C = make_dataclass('Point', ['x', 'y', 'z'])
        c = C(1, 2, 3)
        self.assertEqual(vars(c), {'x': 1, 'y': 2, 'z': 3})

        C = make_dataclass('Point', ['x', ('y', int), 'z'])
        c = C(1, 2, 3)
        self.assertEqual(vars(c), {'x': 1, 'y': 2, 'z': 3})

    def test_init_var(self):

        def post_init(self, y):
            self.x *= y

        C = make_dataclass('C',
                           [('x', int),
                            ('y', InitVar(int)),
                            ],
                           namespace={'__post_init__': post_init},
                           )
        c = C(2, 3)
        self.assertEqual(vars(c), {'x': 6})
        self.assertEqual(len(fields(c)), 1)

    def test_class_var(self):
        from typing import ClassVar
        C = make_dataclass('C',
                           [('x', int),
                            ('y', ClassVar[int], 10),
                            ],
                           )

        self.assertEqual(C.y, 10)
        self.assertEqual(len(fields(C)), 1)

        c = C(5)
        self.assertEqual(c.x, 5)
        self.assertEqual(C.y, 10)

    def test_other_params(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', object, 10),
                            ],
                           init=False)
        # Make sure we have a repr, but no init.
        self.assertNotIn('__init__', vars(C))
        self.assertIn('__repr__', vars(C))

        # Make sure random other params don't work.
        with self.assertRaisesRegexp(TypeError, 'unexpected keyword argument'):
            C = make_dataclass('C',
                               [],
                               xxinit=False)

    def test_keyword_field_names(self):
        for field_name in ['for', 'while', 'if', 'else']:
            with self.subTest(field=field_name):
                with self.assertRaisesRegexp(TypeError, 'must not be keywords'):
                    make_dataclass('C', ['a', field_name])

    def test_non_identifier_field_names(self):
        for field_name in ['()', 'x,y', '*']:
            with self.subTest(field=field_name):
                with self.assertRaisesRegexp(TypeError, 'must be valid identifiers'):
                    make_dataclass('C', ['a', field_name])

    def test_underscore_field_names(self):
        # Unlike namedtuple, it's okay if dataclass field names have an underscore.
        make_dataclass('C', ['_', '_a', 'a_a', 'a_'])

    def test_no_types_get_annotations(self):
        C = make_dataclass('C', ['x', ('y', int), 'z'])
        # Just make sure it doesn't crash
        _ = C(1, 2, 'three')

    def test_no_types_no_typing_import(self):
        # For Python 2, just verify the class is created without issues
        C = make_dataclass('C', ['x', ('y', int)])
        self.assertIsNotNone(C)
        c = C('test_x', 42)
        self.assertEqual(c.x, 'test_x')
        self.assertEqual(c.y, 42)

    def test_invalid_type_specification(self):
        for bad_field in [(), (1, 2, 3, 4)]:
            with self.subTest(bad_field=bad_field):
                with self.assertRaisesRegexp(TypeError, 'Invalid field:'):
                    make_dataclass('C', ['a', bad_field])

    def test_duplicate_field_names(self):
        for field in ['a', 'ab']:
            with self.subTest(field=field):
                with self.assertRaisesRegexp(TypeError, 'Field name duplicated'):
                    make_dataclass('C', [field, 'a', field])

    def test_dataclass_decorator_default(self):
        C = make_dataclass('C', [('x', int)], decorator=dataclass)
        c = C(10)
        self.assertEqual(c.x, 10)

    def test_dataclass_custom_decorator(self):
        def custom_dataclass(cls, *args, **kwargs):
            dc = dataclass(cls, *args, **kwargs)
            dc.__custom__ = True
            return dc

        C = make_dataclass('C', [('x', int)], decorator=custom_dataclass)
        c = C(10)
        self.assertEqual(c.x, 10)
        self.assertEqual(c.__custom__, True)

    def test_funny_class_names_names(self):
        # No reason to prevent weird class names
        for classname in ['()', 'x,y', '*']:
            with self.subTest(classname=classname):
                C = make_dataclass(classname, ['a', 'b'])
                self.assertEqual(C.__name__, classname)

    def test_pickle_support(self):
        # Test that dataclasses created with make_dataclass can be pickled
        C = make_dataclass('C', [('x', int)])
        c = C(10)
        with expose_to_test(C):
            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(proto=proto):
                    pickled = pickle.dumps(c, proto)
                    unpickled = pickle.loads(pickled)
                    self.assertEqual(c, unpickled)
                    self.assertEqual(c.x, unpickled.x)

    def test_cannot_be_pickled(self):
        # Test that dataclasses with wrong module cannot be pickled reliably
        # For Python 2, we just verify basic pickle behavior works
        C = make_dataclass('C', [('x', int)])
        c = C(10)
        with expose_to_test(C):
            # Should be pickleable normally
            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(proto=proto):
                    pickled = pickle.dumps(c, proto)
                    unpickled = pickle.loads(pickled)
                    self.assertEqual(c.x, unpickled.x)

    def test_module_attr(self):
        # Test that module is set correctly
        C = make_dataclass('C', [('x', int)])
        self.assertEqual(C.__module__, __name__)