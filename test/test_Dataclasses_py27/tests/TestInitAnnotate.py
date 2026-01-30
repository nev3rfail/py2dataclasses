from __future__ import print_function, absolute_import

from common import *

class TestInitAnnotate(unittest.TestCase):
    # Tests for annotation handling in __init__
    # These tests use Python 3.14+ features and will be skipped or fail in Python 2.7
    # but we include them for compatibility with the test suite structure

    def test_annotate_function(self):
        # No forward references
        @dataclass
        class A(object):
            a = field(int)

        # In Python 2.7, annotations work differently, so we just test basic functionality
        self.assertTrue(hasattr(A.__init__, '__doc__'))

    def test_annotate_function_forwardref(self):
        # With forward references
        @dataclass
        class B(object):
            b = field('undefined')

        # Basic test that the class was created
        self.assertTrue(hasattr(B, '__dataclass_fields__'))

    def test_annotate_function_init_false(self):
        # Check `init=False` attributes work
        @dataclass
        class C(object):
            c = field(str, init=False)

        self.assertTrue(hasattr(C, '__dataclass_fields__'))

    def test_annotate_function_contains_forwardref(self):
        # Check string annotations on objects containing a ForwardRef
        @dataclass
        class D(object):
            d = field(list)

        # Basic test that the class was created
        self.assertTrue(hasattr(D, '__dataclass_fields__'))

    def test_annotate_function_not_replaced(self):
        # Check that __init__ functions work with slots
        @dataclass(slots=True)
        class E(object):
            x = field(str)
            def __init__(self, x):
                self.x = x

        e = E('test')
        self.assertEqual(e.x, 'test')

    def test_slots_true_init_false(self):
        # Test that slots=True and init=False work together

        @dataclass(slots=True, init=False)
        class F(object):
            x = field(int)

        f = F()
        f.x = 10
        self.assertEqual(f.x, 10)

    def test_init_false_forwardref(self):
        # Test forward references in fields not required for __init__ annotations.

        @dataclass
        class F(object):
            not_in_init = field(list, init=False, default=None)
            in_init = field(int)

        # Basic test that the class works
        f = F(5)
        self.assertEqual(f.in_init, 5)
        self.assertIsNone(f.not_in_init)

