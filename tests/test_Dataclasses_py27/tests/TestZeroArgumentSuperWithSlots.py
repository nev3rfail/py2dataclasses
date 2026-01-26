from __future__ import print_function, absolute_import

from load_test import *

class TestZeroArgumentSuperWithSlots(unittest.TestCase):
    def test_zero_argument_super(self):
        @dataclass(slots=True)
        class A(object):
            def foo(self):
                super(A, self)

        A().foo()

    def test_dunder_class_with_old_property(self):
        @dataclass(slots=True)
        class A(object):
            def _get_foo(slf):
                self.assertIs(A, type(slf))
                self.assertIs(A, slf.__class__)
                return A

            def _set_foo(slf, value):
                self.assertIs(A, type(slf))
                self.assertIs(A, slf.__class__)

            def _del_foo(slf):
                self.assertIs(A, type(slf))
                self.assertIs(A, slf.__class__)

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
                return A

            @foo.setter
            def foo(slf, value):
                self.assertIs(A, type(slf))

            @foo.deleter
            def foo(slf):
                self.assertIs(A, type(slf))

        a = A()
        self.assertIs(a.foo, A)
        a.foo = 4
        del a.foo

    def test_slots_dunder_class_property_getter(self):
        @dataclass(slots=True)
        class A(object):
            @property
            def foo(slf):
                return A

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
        def mydecorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                return f(*args, **kwargs)
            return wrapper

        @dataclass(slots=True)
        class A(object):
            @mydecorator
            def foo(self):
                super(A, self)

        A().foo()

    def test_remembered_class(self):
        # Apply the dataclass decorator manually (not when the class
        # is created), so that we can keep a reference to the
        # undecorated class.
        class A(object):
            def cls(self):
                return A

        self.assertIs(A().cls(), A)

        B = dataclass(slots=True)(A)
        self.assertIs(B().cls(), B)

        # This is undesirable behavior, but is a function of how
        # modifying __class__ in the closure works.  I'm not sure this
        # should be tested or not: I don't really want to guarantee
        # this behavior, but I don't want to lose the point that this
        # is how it works.

        # The underlying class is "broken" by changing its __class__
        # in A.cls() to B.  This normally isn't a problem, because no
        # one will be keeping a reference to the underlying class A.
        self.assertIs(A().cls(), B)

