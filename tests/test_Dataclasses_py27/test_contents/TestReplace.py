from __future__ import print_function, absolute_import

from common import *

class TestReplace(unittest.TestCase):
    def test(self):
        @dataclass(frozen=True)
        class C(object):
            x = field(int)
            y = field(int)

        c = C(1, 2)
        c1 = replace(c, x=3)
        self.assertEqual(c1.x, 3)
        self.assertEqual(c1.y, 2)

    def test_frozen(self):
        @dataclass(frozen=True)
        class C(object):
            x = field(int)
            y = field(int)
            z = field(int, init=False, default=10)
            t = field(int, init=False, default=100)

        c = C(1, 2)
        c1 = replace(c, x=3)
        self.assertEqual((c.x, c.y, c.z, c.t), (1, 2, 10, 100))
        self.assertEqual((c1.x, c1.y, c1.z, c1.t), (3, 2, 10, 100))

        with self.assertRaisesRegexp(TypeError, 'init=False'):
            replace(c, x=3, z=20, t=50)
        with self.assertRaisesRegexp(TypeError, 'init=False'):
            replace(c, z=20)
            replace(c, x=3, z=20, t=50)

        # Make sure the result is still frozen.
        with self.assertRaisesRegexp(FrozenInstanceError, "cannot assign to field 'x'"):
            c1.x = 3

        # Make sure we can't replace an attribute that doesn't exist,
        #  if we're also replacing one that does exist.  Test this
        #  here, because setting attributes on frozen instances is
        #  handled slightly differently from non-frozen ones.
        with self.assertRaisesRegexp(TypeError, r"__init__\(\) got an unexpected "
                                               "keyword argument 'a'"):
            c1 = replace(c, x=20, a=5)

    def test_invalid_field_name(self):
        @dataclass(frozen=True)
        class C(object):
            x = field(int)
            y = field(int)

        c = C(1, 2)
        with self.assertRaisesRegexp(TypeError, r"__init__\(\) got an unexpected "
                                               "keyword argument 'z'"):
            c1 = replace(c, z=3)

    def test_invalid_object(self):
        @dataclass(frozen=True)
        class C(object):
            x = field(int)
            y = field(int)

        with self.assertRaisesRegexp(TypeError, 'dataclass instance'):
            replace(C, x=3)

        with self.assertRaisesRegexp(TypeError, 'dataclass instance'):
            replace(0, x=3)

    def test_no_init(self):
        @dataclass
        class C(object):
            x = field(int)
            y = field(int, init=False, default=10)

        c = C(1)
        c.y = 20

        # Make sure y gets the default value.
        c1 = replace(c, x=5)
        self.assertEqual((c1.x, c1.y), (5, 10))

        # Trying to replace y is an error.
        with self.assertRaisesRegexp(TypeError, 'init=False'):
            replace(c, x=2, y=30)

        with self.assertRaisesRegexp(TypeError, 'init=False'):
            replace(c, y=30)

    def test_classvar(self):
        @dataclass
        class C(object):
            x = field(int)
            y = field(ClassVar[int], default=1000)

        c = C(1)
        d = C(2)

        self.assertIs(c.y, d.y)
        self.assertEqual(c.y, 1000)

        # Trying to replace y is an error: can't replace ClassVars.
        with self.assertRaisesRegexp(TypeError, r"__init__\(\) got an "
                                               "unexpected keyword argument 'y'"):
            replace(c, y=30)

        replace(c, x=5)

    def test_initvar_is_specified(self):
        @dataclass
        class C(object):
            x = field(int)
            y = field(InitVar[int])

            def __post_init__(self, y):
                self.x *= y

        c = C(1, 10)
        self.assertEqual(c.x, 10)
        with self.assertRaisesRegexp(TypeError, r"InitVar 'y' must be "
                                               r"specified with replace\(\)"):
            replace(c, x=3)
        c = replace(c, x=3, y=5)
        self.assertEqual(c.x, 15)

    def test_initvar_with_default_value(self):
        @dataclass
        class C(object):
            x = field(int)
            y = field(InitVar[int], default=None)
            z = field(InitVar[int], default=42)

            def __post_init__(self, y, z):
                if y is not None:
                    self.x += y
                if z is not None:
                    self.x += z

        c = C(x=1, y=10, z=1)
        self.assertEqual(replace(c), C(x=12))
        self.assertEqual(replace(c, y=4), C(x=12, y=4, z=42))
        self.assertEqual(replace(c, y=4, z=1), C(x=12, y=4, z=1))

    def test_recursive_repr(self):
        @dataclass
        class C(object):
            f = field('C')

        c = C(None)
        c.f = c
        # Python 2: check that repr contains the essential parts
        self.assertIn('C(f=...)', repr(c))

    def test_recursive_repr_two_attrs(self):
        @dataclass
        class C(object):
            f = field('C')
            g = field('C')

        c = C(None, None)
        c.f = c
        c.g = c
        # Python 2: check that repr contains the essential parts
        self.assertIn('C(f=..., g=...)', repr(c))

    def test_recursive_repr_indirection(self):
        @dataclass
        class C(object):
            f = field('D')

        @dataclass
        class D(object):
            f = field('C')

        c = C(None)
        d = D(None)
        c.f = d
        d.f = c
        # Python 2: check that repr contains the essential parts
        repr_str = repr(c)
        self.assertIn('C(f=', repr_str)
        self.assertIn('D(f=...)', repr_str)

    def test_recursive_repr_indirection_two(self):
        @dataclass
        class C(object):
            f = field('D')

        @dataclass
        class D(object):
            f = field('E')

        @dataclass
        class E(object):
            f = field('C')

        c = C(None)
        d = D(None)
        e = E(None)
        c.f = d
        d.f = e
        e.f = c
        # Python 2: check that repr contains the essential parts
        repr_str = repr(c)
        self.assertIn('C(f=', repr_str)
        self.assertIn('D(f=', repr_str)
        self.assertIn('E(f=...)', repr_str)

    def test_recursive_repr_misc_attrs(self):
        @dataclass
        class C(object):
            f = field('C')
            g = field(int)

        c = C(None, 1)
        c.f = c
        # Python 2: check that repr contains the essential parts
        self.assertIn('C(f=..., g=1)', repr(c))

