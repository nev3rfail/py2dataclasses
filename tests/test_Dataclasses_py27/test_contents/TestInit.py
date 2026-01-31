from __future__ import print_function, absolute_import

from ..common import *

class TestInit(unittest.TestCase):
    def test_base_has_init(self):
        class B(object):
            def __init__(self):
                self.z = 100

        # Make sure that declaring this class doesn't raise an error.
        #  The issue is that we can't override __init__ in our class,
        #  but it should be okay to add __init__ to us if our base has
        #  an __init__.
        @dataclass
        class C(B):
            x = field(int, default=0)
        c = C(10)
        self.assertEqual(c.x, 10)
        self.assertNotIn('z', vars(c))

        # Make sure that if we don't add an init, the base __init__
        #  gets called.
        @dataclass(init=False)
        class C(B):
            x = field(int, default=10)
        c = C()
        self.assertEqual(c.x, 10)
        self.assertEqual(c.z, 100)

    def test_no_init(self):
        @dataclass(init=False)
        class C(object):
            i = field(int, default=0)
        self.assertEqual(C().i, 0)

        @dataclass(init=False)
        class C(object):
            i = field(int, default=2)
            def __init__(self):
                self.i = 3
        self.assertEqual(C().i, 3)

    def test_overwriting_init(self):
        # If the class has __init__, use it no matter the value of
        #  init=.

        @dataclass
        class C(object):
            x = field(int)
            def __init__(self, x):
                self.x = 2 * x
        self.assertEqual(C(3).x, 6)

        @dataclass(init=True)
        class C(object):
            x = field(int)
            def __init__(self, x):
                self.x = 2 * x
        self.assertEqual(C(4).x, 8)

        @dataclass(init=False)
        class C(object):
            x = field(int)
            def __init__(self, x):
                self.x = 2 * x
        self.assertEqual(C(5).x, 10)

    def test_inherit_from_protocol(self):
        # Dataclasses inheriting from protocol should preserve their own `__init__`.
        # See bpo-45081.
        # Protocol is a typing construct that may not be fully available in py27,
        # so we'll test the basic pattern

        class P(object):
            a = field(int, init=False)

        @dataclass
        class C(P):
            a = field(int)

        self.assertEqual(C(5).a, 5)

        @dataclass
        class D(P):
            def __init__(self, a):
                self.a = a * 2

        self.assertEqual(D(5).a, 10)

