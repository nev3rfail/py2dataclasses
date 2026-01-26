from __future__ import print_function, absolute_import

from load_test import *

class TestDescriptors(unittest.TestCase):
    def test_set_name(self):
        # See bpo-33141.

        # Create a descriptor.
        class D(object):
            def __set_name__(self, owner, name):
                self.name = name + 'x'
            def __get__(self, instance, owner):
                if instance is not None:
                    return 1
                return self

        # This is the case of just normal descriptor behavior, no
        #  dataclass code is involved in initializing the descriptor.
        @dataclass
        class C(object):
            c = field(int, default=D())
        self.assertEqual(C.c.name, 'cx')

        # Now test with a default value and init=False, which is the
        #  only time this is really meaningful.  If not using
        #  init=False, then the descriptor will be overwritten, anyway.
        @dataclass
        class C(object):
            c = field(int, default=D(), init=False)
        self.assertEqual(C.c.name, 'cx')
        self.assertEqual(C().c, 1)

    def test_non_descriptor(self):
        # PEP 487 says __set_name__ should work on non-descriptors.
        # Create a descriptor.

        class D(object):
            def __set_name__(self, owner, name):
                self.name = name + 'x'

        @dataclass
        class C(object):
            c = field(int, default=D(), init=False)
        self.assertEqual(C.c.name, 'cx')

    def test_lookup_on_instance(self):
        # See bpo-33175.
        class D(object):
            pass

        d = D()
        # Create an attribute on the instance, not type.
        d.__set_name__ = lambda owner, name: None

        # Make sure d.__set_name__ is not called.
        @dataclass
        class C(object):
            i = field(int, default=d, init=False)

        # If we got here without error, test passes

    def test_lookup_on_class(self):
        # See bpo-33175.
        class D(object):
            called = False
            def __set_name__(self, owner, name):
                D.called = True

        # Make sure D.__set_name__ is called.
        @dataclass
        class C(object):
            i = field(int, default=D(), init=False)

        self.assertTrue(D.called)

    def test_init_calls_set(self):
        class D(object):
            set_called = False
            def __set__(self, instance, value):
                D.set_called = True

        @dataclass
        class C(object):
            i = field(D, default=D())

        # Make sure D.__set__ is called.
        D.set_called = False
        c = C(D())
        self.assertTrue(D.set_called)

    def test_getting_field_calls_get(self):
        class D(object):
            get_called = False
            def __get__(self, instance, owner):
                D.get_called = True
                return 42
            def __set__(self, instance, value):
                pass

        @dataclass
        class C(object):
            i = field(D, default=D())

        c = C(D())

        # Make sure D.__get__ is called.
        D.get_called = False
        value = c.i
        self.assertTrue(D.get_called)

    def test_setting_field_calls_set(self):
        class D(object):
            set_called = False
            def __set__(self, instance, value):
                D.set_called = True

        @dataclass
        class C(object):
            i = field(D, default=D())

        c = C(D())

        # Make sure D.__set__ is called.
        D.set_called = False
        c.i = 10
        self.assertTrue(D.set_called)

    def test_setting_uninitialized_descriptor_field(self):
        class D(object):
            set_called = False
            def __set__(self, instance, value):
                D.set_called = True

        @dataclass
        class C(object):
            i = field(D)

        # D.__set__ is not called because there's no D instance to call it on
        D.set_called = False
        c = C(D())
        self.assertFalse(D.set_called)

        # D.__set__ still isn't called after setting i to an instance of D
        # because descriptors don't behave like that when stored as instance vars
        c.i = D()
        c.i = 5
        self.assertFalse(D.set_called)

    def test_default_value(self):
        class D(object):
            def __get__(self, instance, owner):
                if instance is None:
                    return 100
                return instance._x

            def __set__(self, instance, value):
                instance._x = value

        @dataclass
        class C(object):
            i = field(D, default=D())

        c = C()
        self.assertEqual(c.i, 100)

        c = C(5)
        self.assertEqual(c.i, 5)

    def test_no_default_value(self):
        class D(object):
            def __get__(self, instance, owner):
                if instance is None:
                    raise AttributeError()
                return instance._x

            def __set__(self, instance, value):
                instance._x = value

        @dataclass
        class C(object):
            i = field(D, default=D())

        with self.assertRaisesRegexp(TypeError, 'missing 1 required positional argument'):
            c = C()

