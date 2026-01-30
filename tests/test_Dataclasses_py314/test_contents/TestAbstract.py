from common import *


class TestAbstract(unittest.TestCase):
    def test_abc_implementation(self):
        class Ordered(abc.ABC):
            @abc.abstractmethod
            def __lt__(self, other):
                pass

            @abc.abstractmethod
            def __le__(self, other):
                pass

        @dataclass(order=True)
        class Date(Ordered):
            year: int
            month: 'Month'
            day: 'int'

        self.assertFalse(inspect.isabstract(Date))
        self.assertGreater(Date(2020,12,25), Date(2020,8,31))

    def test_maintain_abc(self):
        class A(abc.ABC):
            @abc.abstractmethod
            def foo(self):
                pass

        @dataclass
        class Date(A):
            year: int
            month: 'Month'
            day: 'int'

        self.assertTrue(inspect.isabstract(Date))
        msg = "class Date without an implementation for abstract method 'foo'"
        self.assertRaisesRegex(TypeError, msg, Date)
