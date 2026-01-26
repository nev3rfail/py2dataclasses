from load_test import *

class TestRepr(unittest.TestCase):
    def test_repr(self):
        @dataclass
        class B(object):
            x = field(int)

        @dataclass
        class C(B):
            y = field(int, default=10)

        o = C(4)
        # Basic repr test - just verify it contains the values
        repr_str = repr(o)
        self.assertIn('C', repr_str)
        self.assertIn('4', repr_str)
        self.assertIn('10', repr_str)

        @dataclass
        class D(C):
            x = field(int, default=20)
        repr_str = repr(D())
        self.assertIn('D', repr_str)
        self.assertIn('20', repr_str)
        self.assertIn('10', repr_str)

    def test_no_repr(self):
        # Test a class with no __repr__ and repr=False.
        @dataclass(repr=False)
        class C(object):
            x = field(int)
        repr_str = repr(C(3))
        self.assertIn('C object at', repr_str)

        # Test a class with a __repr__ and repr=False.
        @dataclass(repr=False)
        class C(object):
            x = field(int)
            def __repr__(self):
                return 'C-class'
        self.assertEqual(repr(C(3)), 'C-class')

    def test_overwriting_repr(self):
        # If the class has __repr__, use it no matter the value of
        #  repr=.

        @dataclass
        class C(object):
            x = field(int)
            def __repr__(self):
                return 'x'
        self.assertEqual(repr(C(0)), 'x')

        @dataclass(repr=True)
        class C(object):
            x = field(int)
            def __repr__(self):
                return 'x'
        self.assertEqual(repr(C(0)), 'x')

        @dataclass(repr=False)
        class C(object):
            x = field(int)
            def __repr__(self):
                return 'x'
        self.assertEqual(repr(C(0)), 'x')