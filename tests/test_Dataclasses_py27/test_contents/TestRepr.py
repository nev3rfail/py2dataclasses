from __future__ import print_function, absolute_import

from ..common import *

class TestRepr(unittest.TestCase):
    def test_repr(self):
        @dataclass
        class B(object):
            x = field(int)

        @dataclass
        class C(B):
            y = field(int, default=10)

        o = C(4)
        # Python 2 doesn't have __qualname__, so we check for the module-qualified name
        self.assertIn('C(x=4, y=10)', repr(o))

        @dataclass
        class D(C):
            x = field(int, default=20)
        self.assertIn('D(x=20, y=10)', repr(D()))

        @dataclass
        class C(object):
            @dataclass
            class D(object):
                i = field(int)
            @dataclass
            class E(object):
                pass
        # Python 2 doesn't have __qualname__
        self.assertIn('C.D(i=0)', repr(C.D(0)))
        self.assertIn('C.E()', repr(C.E()))

    def test_no_repr(self):
        # Test a class with no __repr__ and repr=False.
        @dataclass(repr=False)
        class C(object):
            x = field(int)
        # Python 2 doesn't have __qualname__, so we just check for 'object at'
        self.assertIn('object at', repr(C(3)))

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