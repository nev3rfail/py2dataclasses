from __future__ import print_function, absolute_import

import abc

import six

from ..common import *


class TestAbstract(unittest.TestCase):
    def test_abc_implementation(self):
        class Ordered(ABC):
            @abc.abstractmethod
            def __lt__(self, other):
                pass

            @abc.abstractmethod
            def __le__(self, other):
                pass

        @dataclass(order=True)
        class Date(Ordered):
            year = field(int)
            month = field(str)
            day = field(int)

        self.assertFalse(inspect.isabstract(Date))
        self.assertGreater(Date(2020, 12, 25), Date(2020, 8, 31))

    def test_maintain_abc(self):
        class A(ABC):
            @abc.abstractmethod
            def foo(self):
                pass
        class Date2(object):

            year = field(int)
            month = field(str)
            day = field(int)
        @dataclass
        class Date(A):
            year = field(int)
            month = field(str)
            day = field(int)

        self.assertTrue(inspect.isabstract(Date))
        if six.PY3:
            msg = "class Date without an implementation for abstract method 'foo'"
        elif six.PY2:
            msg = "Can't instantiate abstract class Date with abstract methods foo"
        self.assertRaisesRegexp(TypeError, msg, Date)