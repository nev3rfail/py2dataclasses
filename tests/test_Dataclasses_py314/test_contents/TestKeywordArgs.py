from ..common import *
class TestKeywordArgs(unittest.TestCase):
    def test_no_classvar_kwarg(self):
        msg = 'field a is a ClassVar but specifies kw_only'
        with self.assertRaisesRegex(TypeError, msg):
            @dataclass
            class A:
                a: ClassVar[int] = field(kw_only=True)

        with self.assertRaisesRegex(TypeError, msg):
            @dataclass
            class A:
                a: ClassVar[int] = field(kw_only=False)

        with self.assertRaisesRegex(TypeError, msg):
            @dataclass(kw_only=True)
            class A:
                a: ClassVar[int] = field(kw_only=False)

    def test_field_marked_as_kwonly(self):
        #######################
        # Using dataclass(kw_only=True)
        @dataclass(kw_only=True)
        class A:
            a: int
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass(kw_only=True)
        class A:
            a: int = field(kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass(kw_only=True)
        class A:
            a: int = field(kw_only=False)
        self.assertFalse(fields(A)[0].kw_only)

        #######################
        # Using dataclass(kw_only=False)
        @dataclass(kw_only=False)
        class A:
            a: int
        self.assertFalse(fields(A)[0].kw_only)

        @dataclass(kw_only=False)
        class A:
            a: int = field(kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass(kw_only=False)
        class A:
            a: int = field(kw_only=False)
        self.assertFalse(fields(A)[0].kw_only)

        #######################
        # Not specifying dataclass(kw_only)
        @dataclass
        class A:
            a: int
        self.assertFalse(fields(A)[0].kw_only)

        @dataclass
        class A:
            a: int = field(kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass
        class A:
            a: int = field(kw_only=False)
        self.assertFalse(fields(A)[0].kw_only)

    def test_match_args(self):
        # kw fields don't show up in __match_args__.
        @dataclass(kw_only=True)
        class C:
            a: int
        self.assertEqual(C(a=42).__match_args__, ())

        @dataclass
        class C:
            a: int
            b: int = field(kw_only=True)
        self.assertEqual(C(42, b=10).__match_args__, ('a',))

    def test_KW_ONLY(self):
        @dataclass
        class A:
            a: int
            _: KW_ONLY
            b: int
            c: int
        A(3, c=5, b=4)
        msg = "takes 2 positional arguments but 4 were given"
        with self.assertRaisesRegex(TypeError, msg):
            A(3, 4, 5)


        @dataclass(kw_only=True)
        class B:
            a: int
            _: KW_ONLY
            b: int
            c: int
        B(a=3, b=4, c=5)
        msg = "takes 1 positional argument but 4 were given"
        with self.assertRaisesRegex(TypeError, msg):
            B(3, 4, 5)

        # Explicitly make a field that follows KW_ONLY be non-keyword-only.
        @dataclass
        class C:
            a: int
            _: KW_ONLY
            b: int
            c: int = field(kw_only=False)
        c = C(1, 2, b=3)
        self.assertEqual(c.a, 1)
        self.assertEqual(c.b, 3)
        self.assertEqual(c.c, 2)
        c = C(1, b=3, c=2)
        self.assertEqual(c.a, 1)
        self.assertEqual(c.b, 3)
        self.assertEqual(c.c, 2)
        c = C(1, b=3, c=2)
        self.assertEqual(c.a, 1)
        self.assertEqual(c.b, 3)
        self.assertEqual(c.c, 2)
        c = C(c=2, b=3, a=1)
        self.assertEqual(c.a, 1)
        self.assertEqual(c.b, 3)
        self.assertEqual(c.c, 2)

    def test_KW_ONLY_as_string(self):
        @dataclass
        class A:
            a: int
            _: 'dataclasses.KW_ONLY'
            b: int
            c: int
        A(3, c=5, b=4)
        msg = "takes 2 positional arguments but 4 were given"
        with self.assertRaisesRegex(TypeError, msg):
            A(3, 4, 5)

    def test_KW_ONLY_twice(self):
        msg = "'Y' is KW_ONLY, but KW_ONLY has already been specified"

        with self.assertRaisesRegex(TypeError, msg):
            @dataclass
            class A:
                a: int
                X: KW_ONLY
                Y: KW_ONLY
                b: int
                c: int

        with self.assertRaisesRegex(TypeError, msg):
            @dataclass
            class A:
                a: int
                X: KW_ONLY
                b: int
                Y: KW_ONLY
                c: int

        with self.assertRaisesRegex(TypeError, msg):
            @dataclass
            class A:
                a: int
                X: KW_ONLY
                b: int
                c: int
                Y: KW_ONLY

        # But this usage is okay, since it's not using KW_ONLY.
        @dataclass
        class NoDuplicateKwOnlyAnnotation:
            a: int
            _: KW_ONLY
            b: int
            c: int = field(kw_only=True)

        # And if inheriting, it's okay.
        @dataclass
        class BaseUsesKwOnly:
            a: int
            _: KW_ONLY
            b: int
            c: int
        @dataclass
        class SubclassUsesKwOnly(BaseUsesKwOnly):
            _: KW_ONLY
            d: int

        # Make sure the error is raised in a derived class.
        with self.assertRaisesRegex(TypeError, msg):
            @dataclass
            class A:
                a: int
                _: KW_ONLY
                b: int
                c: int
            @dataclass
            class B(A):
                X: KW_ONLY
                d: int
                Y: KW_ONLY


    def test_post_init(self):
        @dataclass
        class A:
            a: int
            _: KW_ONLY
            b: InitVar[int]
            c: int
            d: InitVar[int]
            def __post_init__(self, b, d):
                raise CustomError(f'{b=} {d=}')
        with self.assertRaisesRegex(CustomError, 'b=3 d=4'):
            A(1, c=2, b=3, d=4)

        @dataclass
        class B:
            a: int
            _: KW_ONLY
            b: InitVar[int]
            c: int
            d: InitVar[int]
            def __post_init__(self, b, d):
                self.a = b
                self.c = d
        b = B(1, c=2, b=3, d=4)
        self.assertEqual(asdict(b), {'a': 3, 'c': 4})

    def test_defaults(self):
        # For kwargs, make sure we can have defaults after non-defaults.
        @dataclass
        class A:
            a: int = 0
            _: KW_ONLY
            b: int
            c: int = 1
            d: int

        a = A(d=4, b=3)
        self.assertEqual(a.a, 0)
        self.assertEqual(a.b, 3)
        self.assertEqual(a.c, 1)
        self.assertEqual(a.d, 4)

        # Make sure we still check for non-kwarg non-defaults not following
        # defaults.
        err_regex = "non-default argument 'z' follows default argument 'a'"
        with self.assertRaisesRegex(TypeError, err_regex):
            @dataclass
            class A:
                a: int = 0
                z: int
                _: KW_ONLY
                b: int
                c: int = 1
                d: int

    def test_make_dataclass(self):
        A = make_dataclass("A", ['a'], kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        B = make_dataclass("B",
                           ['a', ('b', int, field(kw_only=False))],
                           kw_only=True)
        self.assertTrue(fields(B)[0].kw_only)
        self.assertFalse(fields(B)[1].kw_only)

    def test_deferred_annotations(self):
        @dataclass
        class A:
            x: undefined
            y: ClassVar[undefined]

        fs = fields(A)
        self.assertEqual(len(fs), 1)
        self.assertEqual(fs[0].name, 'x')
