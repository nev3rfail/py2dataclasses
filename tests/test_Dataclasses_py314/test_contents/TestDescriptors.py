from common import *

class TestDescriptors(unittest.TestCase):
    def test_set_name(self):
        # See bpo-33141.

        # Create a descriptor.
        class D:
            def __set_name__(self, owner, name):
                self.name = name + 'x'
            def __get__(self, instance, owner):
                if instance is not None:
                    return 1
                return self

        # This is the case of just normal descriptor behavior, no
        #  dataclass code is involved in initializing the descriptor.
        @dataclass
        class C:
            c: int=D()
        self.assertEqual(C.c.name, 'cx')

        # Now test with a default value and init=False, which is the
        #  only time this is really meaningful.  If not using
        #  init=False, then the descriptor will be overwritten, anyway.
        @dataclass
        class C:
            c: int=field(default=D(), init=False)
        self.assertEqual(C.c.name, 'cx')
        self.assertEqual(C().c, 1)

    def test_non_descriptor(self):
        # PEP 487 says __set_name__ should work on non-descriptors.
        # Create a descriptor.

        class D:
            def __set_name__(self, owner, name):
                self.name = name + 'x'

        @dataclass
        class C:
            c: int=field(default=D(), init=False)
        self.assertEqual(C.c.name, 'cx')

    def test_lookup_on_instance(self):
        # See bpo-33175.
        class D:
            pass

        d = D()
        # Create an attribute on the instance, not type.
        d.__set_name__ = Mock()

        # Make sure d.__set_name__ is not called.
        @dataclass
        class C:
            i: int=field(default=d, init=False)

        self.assertEqual(d.__set_name__.call_count, 0)

    def test_lookup_on_class(self):
        # See bpo-33175.
        class D:
            pass
        D.__set_name__ = Mock()

        # Make sure D.__set_name__ is called.
        @dataclass
        class C:
            i: int=field(default=D(), init=False)

        self.assertEqual(D.__set_name__.call_count, 1)

    def test_init_calls_set(self):
        class D:
            pass

        D.__set__ = Mock()

        @dataclass
        class C:
            i: D = D()

        # Make sure D.__set__ is called.
        D.__set__.reset_mock()
        c = C(5)
        self.assertEqual(D.__set__.call_count, 1)

    def test_getting_field_calls_get(self):
        class D:
            pass

        D.__set__ = Mock()
        D.__get__ = Mock()

        @dataclass
        class C:
            i: D = D()

        c = C(5)

        # Make sure D.__get__ is called.
        D.__get__.reset_mock()
        value = c.i
        self.assertEqual(D.__get__.call_count, 1)

    def test_setting_field_calls_set(self):
        class D:
            pass

        D.__set__ = Mock()

        @dataclass
        class C:
            i: D = D()

        c = C(5)

        # Make sure D.__set__ is called.
        D.__set__.reset_mock()
        c.i = 10
        self.assertEqual(D.__set__.call_count, 1)

    def test_setting_uninitialized_descriptor_field(self):
        class D:
            pass

        D.__set__ = Mock()

        @dataclass
        class C:
            i: D

        # D.__set__ is not called because there's no D instance to call it on
        D.__set__.reset_mock()
        c = C(5)
        self.assertEqual(D.__set__.call_count, 0)

        # D.__set__ still isn't called after setting i to an instance of D
        # because descriptors don't behave like that when stored as instance vars
        c.i = D()
        c.i = 5
        self.assertEqual(D.__set__.call_count, 0)

    def test_default_value(self):
        class D:
            def __get__(self, instance: Any, owner: object) -> int:
                if instance is None:
                    return 100

                return instance._x

            def __set__(self, instance: Any, value: int) -> None:
                instance._x = value

        @dataclass
        class C:
            i: D = D()

        c = C()
        self.assertEqual(c.i, 100)

        c = C(5)
        self.assertEqual(c.i, 5)

    def test_no_default_value(self):
        class D:
            def __get__(self, instance: Any, owner: object) -> int:
                if instance is None:
                    raise AttributeError()

                return instance._x

            def __set__(self, instance: Any, value: int) -> None:
                instance._x = value

        @dataclass
        class C:
            i: D = D()

        with self.assertRaisesRegex(TypeError, 'missing 1 required positional argument'):
            c = C()
