from load_test import *

class TestZeroArgumentSuperWithSlots(unittest.TestCase):
    def test_zero_argument_super(self):
        @dataclass(slots=True)
        class A(object):
            def foo(self):
                # In Python 3 this is valid; in Python 2 this may fail, as allowed.
                super()

        A().foo()

    def test_dunder_class_with_old_property(self):
        @dataclass(slots=True)
        class A(object):
            def _get_foo(slf):
                self.assertIs(__class__, type(slf))
                self.assertIs(__class__, slf.__class__)
                return __class__

            def _set_foo(slf, value):
                self.assertIs(__class__, type(slf))
                self.assertIs(__class__, slf.__class__)

            def _del_foo(slf):
                self.assertIs(__class__, type(slf))
                self.assertIs(__class__, slf.__class__)

            foo = property(_get_foo, _set_foo, _del_foo)

        a = A()
        self.assertIs(a.foo, A)
        a.foo = 4
        del a.foo

    def test_dunder_class_with_new_property(self):
        @dataclass(slots=True)
        class A(object):
            @property
            def foo(slf):
                return slf.__class__

            @foo.setter
            def foo(slf, value):
                self.assertIs(__class__, type(slf))

            @foo.deleter
            def foo(slf):
                self.assertIs(__class__, type(slf))

        a = A()
        self.assertIs(a.foo, A)
        a.foo = 4
        del a.foo

    # Test the parts of a property individually.
    def test_slots_dunder_class_property_getter(self):
        @dataclass(slots=True)
        class A(object):
            @property
            def foo(slf):
                return __class__

        a = A()
        self.assertIs(a.foo, A)

    def test_slots_dunder_class_property_setter(self):
        @dataclass(slots=True)
        class A(object):
            foo = property()
            @foo.setter
            def foo(slf, val):
                self.assertIs(__class__, type(slf))

        a = A()
        a.foo = 4

    def test_slots_dunder_class_property_deleter(self):
        @dataclass(slots=True)
        class A(object):
            foo = property()
            @foo.deleter
            def foo(slf):
                self.assertIs(__class__, type(slf))

        a = A()
        del a.foo

    def test_wrapped(self):
        from functools import wraps
        def mydecorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapper

        @dataclass(slots=True)
        class A(object):
            @mydecorator
            def foo(self):
                super()

        A().foo()

    def test_remembered_class(self):
        # Apply the dataclass decorator manually (not when the class
        # is created), so that we can keep a reference to the
        # undecorated class.
        class A(object):
            def cls(self):
                return __class__

        self.assertIs(A().cls(), A)

        B = dataclass(slots=True)(A)
        self.assertIs(B().cls(), B)

        # The underlying class is affected similarly as in CPython tests
        self.assertIs(A().cls(), B)

