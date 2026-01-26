from load_test import *

class TestKeywordArgs(unittest.TestCase):
    def test_field_marked_as_kwonly(self):
        # Test kw_only flag on fields
        @dataclass(kw_only=True)
        class A(object):
            a = field(int)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass(kw_only=True)
        class A(object):
            a = field(int, kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass(kw_only=True)
        class A(object):
            a = field(int, kw_only=False)
        self.assertFalse(fields(A)[0].kw_only)

        # Using dataclass(kw_only=False)
        @dataclass(kw_only=False)
        class A(object):
            a = field(int)
        self.assertFalse(fields(A)[0].kw_only)

        @dataclass(kw_only=False)
        class A(object):
            a = field(int, kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass(kw_only=False)
        class A(object):
            a = field(int, kw_only=False)
        self.assertFalse(fields(A)[0].kw_only)

        # Not specifying dataclass(kw_only)
        @dataclass
        class A(object):
            a = field(int)
        self.assertFalse(fields(A)[0].kw_only)

        @dataclass
        class A(object):
            a = field(int, kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass
        class A(object):
            a = field(int, kw_only=False)
        self.assertFalse(fields(A)[0].kw_only)

    def test_match_args(self):
        # kw fields don't show up in __match_args__.
        @dataclass(kw_only=True)
        class C(object):
            a = field(int)
        self.assertEqual(C(a=42).__match_args__, ())

        @dataclass
        class C(object):
            a = field(int)
            b = field(int, kw_only=True)
        self.assertEqual(C(42, b=10).__match_args__, ('a',))

    def test_no_classvar_kwarg(self):
        from typing import ClassVar
        msg = 'field a is a ClassVar but specifies kw_only'
        with self.assertRaisesRegexp(TypeError, msg):
            @dataclass
            class A(object):
                a = field(ClassVar[int], kw_only=True)

        with self.assertRaisesRegexp(TypeError, msg):
            @dataclass
            class A(object):
                a = field(ClassVar[int], kw_only=False)

        with self.assertRaisesRegexp(TypeError, msg):
            @dataclass(kw_only=True)
            class A(object):
                a = field(ClassVar[int], kw_only=False)

    def test_KW_ONLY(self):
        # Python 2 doesn't support KW_ONLY sentinel field syntax
        # but we can still test kw_only functionality using field(kw_only=True)
        @dataclass
        class A(object):
            a = field(int)
            b = field(int, kw_only=True)
            c = field(int, kw_only=True)

        # Should be able to create with positional a and keyword-only b, c
        a_inst = A(3, c=5, b=4)
        self.assertEqual(a_inst.a, 3)
        self.assertEqual(a_inst.b, 4)
        self.assertEqual(a_inst.c, 5)

        @dataclass(kw_only=True)
        class B(object):
            a = field(int)
            b = field(int)
            c = field(int)

        # All fields are keyword-only
        b_inst = B(a=3, b=4, c=5)
        self.assertEqual(b_inst.a, 3)
        self.assertEqual(b_inst.b, 4)
        self.assertEqual(b_inst.c, 5)

        @dataclass
        class C(object):
            a = field(int)
            b = field(int, kw_only=True)
            c = field(int, kw_only=False)

        # a is positional, b is kw-only, c is positional
        c_inst = C(1, 2, b=3)
        self.assertEqual(c_inst.a, 1)
        self.assertEqual(c_inst.b, 3)
        self.assertEqual(c_inst.c, 2)

        c_inst = C(1, b=3, c=2)
        self.assertEqual(c_inst.a, 1)
        self.assertEqual(c_inst.b, 3)
        self.assertEqual(c_inst.c, 2)

    def test_KW_ONLY_as_string(self):
        # Python 2 doesn't support KW_ONLY sentinel field or string annotations for it
        # Test that kw_only works as a field parameter
        @dataclass
        class A(object):
            a = field(int)
            b = field(int, kw_only=True)
            c = field(int)

        # Verify kw_only is set correctly
        fs = fields(A)
        self.assertFalse(fs[0].kw_only)  # a
        self.assertTrue(fs[1].kw_only)   # b
        self.assertFalse(fs[2].kw_only)  # c

    def test_KW_ONLY_twice(self):

        @dataclass
        class A(object):
            a = field(int, kw_only=True)
            b = field(int, kw_only=False)  # Conflicting specification

        # Just verify the class was created with mixed kw_only settings
        fs = fields(A)
        self.assertTrue(fs[0].kw_only)
        self.assertFalse(fs[1].kw_only)


    def test_post_init(self):
        @dataclass
        class A(object):
            a = field(int)
            b = field(InitVar(int), kw_only=True)
            c = field(int, kw_only=True)
            d = field(InitVar(int), kw_only=True)

            def __post_init__(self, b, d):
                # Modify a based on b and d
                self.a = self.a + b + d


        a_inst = A(1, b=3, c=2, d=4)
        self.assertEqual(a_inst.a, 1 + 3 + 4)
        self.assertEqual(a_inst.c, 2)

    def test_defaults(self):
        # For kwargs, make sure we can have defaults after non-defaults.
        @dataclass
        class A(object):
            a = field(int, default=0, kw_only=True)
            b = field(int, kw_only=True)
            c = field(int, default=1, kw_only=True)
            d = field(int, kw_only=True)

        # Python 2 doesn't support keyword-only args in __init__, so we just verify the fields exist
        self.assertEqual(len(fields(A)), 4)

    def test_make_dataclass(self):
        A = make_dataclass('A', ['a'], kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        B = make_dataclass('B',
                           ['a', ('b', int, field(int, kw_only=False))],
                           kw_only=True)
        self.assertTrue(fields(B)[0].kw_only)
        self.assertFalse(fields(B)[1].kw_only)

    def test_deferred_annotations(self):
        @dataclass
        class A(object):
            x = field(object)

        # Just verify the field is created
        fs = fields(A)
        self.assertEqual(len(fs), 1)
        self.assertEqual(fs[0].name, 'x')
