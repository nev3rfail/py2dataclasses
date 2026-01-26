from load_test import *

class TestAbstract(unittest.TestCase):
    def test_abc_implementation(self):
        #
        import inspect

        class Ordered(object):
            __metaclass__ = abc.ABCMeta
            @abc.abstractmethod
            def __lt__(self, other):
                pass

            @abc.abstractmethod
            def __le__(self, other):
                pass

        @dataclass(order=True)
        class Date(Ordered):
            """yay doc"""
            year = field(int)
            month = field(str)
            day = field(int)

        self.assertFalse(inspect.isabstract(Date))
        self.assertGreater(Date(2020, 12, 25), Date(2020, 8, 31))

    def test_maintain_abc(self):

        import inspect

        class A(ABC):
            @abc.abstractmethod
            def foo(self):
                pass

        @dataclass
        class Date(A):
            year = field(int)
            month = field(str)
            day = field(int)

        self.assertTrue(inspect.isabstract(Date))
        msg = "Can't instantiate abstract class Date with abstract methods foo"
        self.assertRaisesRegexp(TypeError, msg, Date)