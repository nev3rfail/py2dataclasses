from ..common import *

class TestMatchArgs(unittest.TestCase):
    def test_match_args(self):
        @dataclass
        class C:
            a: int
        self.assertEqual(C(42).__match_args__, ('a',))

    def test_explicit_match_args(self):
        ma = ()
        @dataclass
        class C:
            a: int
            __match_args__ = ma
        self.assertIs(C(42).__match_args__, ma)

    def test_bpo_43764(self):
        @dataclass(repr=False, eq=False, init=False)
        class X:
            a: int
            b: int
            c: int
        self.assertEqual(X.__match_args__, ("a", "b", "c"))

    def test_match_args_argument(self):
        @dataclass(match_args=False)
        class X:
            a: int
        self.assertNotIn('__match_args__', X.__dict__)

        @dataclass(match_args=False)
        class Y:
            a: int
            __match_args__ = ('b',)
        self.assertEqual(Y.__match_args__, ('b',))

        @dataclass(match_args=False)
        class Z(Y):
            z: int
        self.assertEqual(Z.__match_args__, ('b',))

        # Ensure parent dataclass __match_args__ is seen, if child class
        # specifies match_args=False.
        @dataclass
        class A:
            a: int
            z: int
        @dataclass(match_args=False)
        class B(A):
            b: int
        self.assertEqual(B.__match_args__, ('a', 'z'))

    def test_make_dataclasses(self):
        C = make_dataclass('C', [('x', int), ('y', int)])
        self.assertEqual(C.__match_args__, ('x', 'y'))

        C = make_dataclass('C', [('x', int), ('y', int)], match_args=True)
        self.assertEqual(C.__match_args__, ('x', 'y'))

        C = make_dataclass('C', [('x', int), ('y', int)], match_args=False)
        self.assertNotIn('__match__args__', C.__dict__)

        C = make_dataclass('C', [('x', int), ('y', int)], namespace={'__match_args__': ('z',)})
        self.assertEqual(C.__match_args__, ('z',))
