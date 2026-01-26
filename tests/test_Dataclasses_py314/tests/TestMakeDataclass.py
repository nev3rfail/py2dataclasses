from load_test import *

ByMakeDataClass = make_dataclass('ByMakeDataClass', [('x', int)])
ManualModuleMakeDataClass = make_dataclass('ManualModuleMakeDataClass',
                                           [('x', int)],
                                           module=__name__)
WrongNameMakeDataclass = make_dataclass('Wrong', [('x', int)])
WrongModuleMakeDataclass = make_dataclass('WrongModuleMakeDataclass',
                                          [('x', int)],
                                          module='custom')

class TestMakeDataclass(unittest.TestCase):
    def test_simple(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', int, field(default=5))],
                           namespace={'add_one': lambda self: self.x + 1})
        c = C(10)
        self.assertEqual((c.x, c.y), (10, 5))
        self.assertEqual(c.add_one(), 11)


    def test_no_mutate_namespace(self):
        # Make sure a provided namespace isn't mutated.
        ns = {}
        C = make_dataclass('C',
                           [('x', int),
                            ('y', int, field(default=5))],
                           namespace=ns)
        self.assertEqual(ns, {})

    def test_base(self):
        class Base1:
            pass
        class Base2:
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
        class Base1:
            x: int
        class Base2:
            pass
        C = make_dataclass('C',
                           [('y', int)],
                           bases=(Base1, Base2))
        with self.assertRaisesRegex(TypeError, 'required positional'):
            c = C(2)
        c = C(1, 2)
        self.assertIsInstance(c, C)
        self.assertIsInstance(c, Base1)
        self.assertIsInstance(c, Base2)

        self.assertEqual((c.x, c.y), (1, 2))

    def test_init_var(self):
        def post_init(self, y):
            self.x *= y

        C = make_dataclass('C',
                           [('x', int),
                            ('y', InitVar[int]),
                            ],
                           namespace={'__post_init__': post_init},
                           )
        c = C(2, 3)
        self.assertEqual(vars(c), {'x': 6})
        self.assertEqual(len(fields(c)), 1)

    def test_class_var(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', ClassVar[int], 10),
                            ('z', ClassVar[int], field(default=20)),
                            ])
        c = C(1)
        self.assertEqual(vars(c), {'x': 1})
        self.assertEqual(len(fields(c)), 1)
        self.assertEqual(C.y, 10)
        self.assertEqual(C.z, 20)

    def test_other_params(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', ClassVar[int], 10),
                            ('z', ClassVar[int], field(default=20)),
                            ],
                           init=False)
        # Make sure we have a repr, but no init.
        self.assertNotIn('__init__', vars(C))
        self.assertIn('__repr__', vars(C))

        # Make sure random other params don't work.
        with self.assertRaisesRegex(TypeError, 'unexpected keyword argument'):
            C = make_dataclass('C',
                               [],
                               xxinit=False)

    def test_no_types(self):
        C = make_dataclass('Point', ['x', 'y', 'z'])
        c = C(1, 2, 3)
        self.assertEqual(vars(c), {'x': 1, 'y': 2, 'z': 3})
        self.assertEqual(C.__annotations__, {'x': typing.Any,
                                             'y': typing.Any,
                                             'z': typing.Any})

        C = make_dataclass('Point', ['x', ('y', int), 'z'])
        c = C(1, 2, 3)
        self.assertEqual(vars(c), {'x': 1, 'y': 2, 'z': 3})
        self.assertEqual(C.__annotations__, {'x': typing.Any,
                                             'y': int,
                                             'z': typing.Any})

    def test_no_types_get_annotations(self):
        C = make_dataclass('C', ['x', ('y', int), 'z'])

        self.assertEqual(
            annotationlib.get_annotations(C, format=annotationlib.Format.VALUE),
            {'x': typing.Any, 'y': int, 'z': typing.Any},
        )
        self.assertEqual(
            annotationlib.get_annotations(
                C, format=annotationlib.Format.FORWARDREF),
            {'x': typing.Any, 'y': int, 'z': typing.Any},
        )
        self.assertEqual(
            annotationlib.get_annotations(
                C, format=annotationlib.Format.STRING),
            {'x': 'typing.Any', 'y': 'int', 'z': 'typing.Any'},
        )

    def test_no_types_no_typing_import(self):
        with import_helper.CleanImport('typing'):
            self.assertNotIn('typing', sys.modules)
            C = make_dataclass('C', ['x', ('y', int)])

            self.assertNotIn('typing', sys.modules)
            self.assertEqual(
                C.__annotate__(annotationlib.Format.FORWARDREF),
                {
                    'x': annotationlib.ForwardRef('Any', module='typing'),
                    'y': int,
                },
            )
            self.assertNotIn('typing', sys.modules)

            for field in fields(C):
                if field.name == "x":
                    self.assertEqual(field.type, annotationlib.ForwardRef('Any', module='typing'))
                else:
                    self.assertEqual(field.name, "y")
                    self.assertIs(field.type, int)

    def test_module_attr(self):
        self.assertEqual(ByMakeDataClass.__module__, __name__)
        self.assertEqual(ByMakeDataClass(1).__module__, __name__)
        self.assertEqual(WrongModuleMakeDataclass.__module__, "custom")
        Nested = make_dataclass('Nested', [])
        self.assertEqual(Nested.__module__, __name__)
        self.assertEqual(Nested().__module__, __name__)

    def test_pickle_support(self):
        for klass in [ByMakeDataClass, ManualModuleMakeDataClass]:
            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(proto=proto):
                    self.assertEqual(
                        pickle.loads(pickle.dumps(klass, proto)),
                        klass,
                    )
                    self.assertEqual(
                        pickle.loads(pickle.dumps(klass(1), proto)),
                        klass(1),
                    )

    def test_cannot_be_pickled(self):
        for klass in [WrongNameMakeDataclass, WrongModuleMakeDataclass]:
            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(proto=proto):
                    with self.assertRaises(pickle.PickleError):
                        pickle.dumps(klass, proto)
                    with self.assertRaises(pickle.PickleError):
                        pickle.dumps(klass(1), proto)

    def test_invalid_type_specification(self):
        for bad_field in [(),
                          (1, 2, 3, 4),
                          ]:
            with self.subTest(bad_field=bad_field):
                with self.assertRaisesRegex(TypeError, r'Invalid field: '):
                    make_dataclass('C', ['a', bad_field])

        # And test for things with no len().
        for bad_field in [float,
                          lambda x:x,
                          ]:
            with self.subTest(bad_field=bad_field):
                with self.assertRaisesRegex(TypeError, r'has no len\(\)'):
                    make_dataclass('C', ['a', bad_field])

    def test_duplicate_field_names(self):
        for field in ['a', 'ab']:
            with self.subTest(field=field):
                with self.assertRaisesRegex(TypeError, 'Field name duplicated'):
                    make_dataclass('C', [field, 'a', field])

    def test_keyword_field_names(self):
        for field in ['for', 'async', 'await', 'as']:
            with self.subTest(field=field):
                with self.assertRaisesRegex(TypeError, 'must not be keywords'):
                    make_dataclass('C', ['a', field])
                with self.assertRaisesRegex(TypeError, 'must not be keywords'):
                    make_dataclass('C', [field])
                with self.assertRaisesRegex(TypeError, 'must not be keywords'):
                    make_dataclass('C', [field, 'a'])

    def test_non_identifier_field_names(self):
        for field in ['()', 'x,y', '*', '2@3', '', 'little johnny tables']:
            with self.subTest(field=field):
                with self.assertRaisesRegex(TypeError, 'must be valid identifiers'):
                    make_dataclass('C', ['a', field])
                with self.assertRaisesRegex(TypeError, 'must be valid identifiers'):
                    make_dataclass('C', [field])
                with self.assertRaisesRegex(TypeError, 'must be valid identifiers'):
                    make_dataclass('C', [field, 'a'])

    def test_underscore_field_names(self):
        # Unlike namedtuple, it's okay if dataclass field names have
        # an underscore.
        make_dataclass('C', ['_', '_a', 'a_a', 'a_'])

    def test_funny_class_names_names(self):
        # No reason to prevent weird class names, since
        # types.new_class allows them.
        for classname in ['()', 'x,y', '*', '2@3', '']:
            with self.subTest(classname=classname):
                C = make_dataclass(classname, ['a', 'b'])
                self.assertEqual(C.__name__, classname)

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
