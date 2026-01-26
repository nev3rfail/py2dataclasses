from load_test import *

class TestEq(unittest.TestCase):
    def test_recursive_eq(self):
        # Test a class with recursive child
        @dataclass
        class C(object):
            recursive = field(object, default=types.EllipsisType)
        c = C()
        c.recursive = c
        self.assertEqual(c, c)

    def test_no_eq(self):
        # Test a class with no __eq__ and eq=False.
        @dataclass(eq=False)
        class C(object):
            x = field(int)
        self.assertNotEqual(C(0), C(0))
        c = C(3)
        self.assertEqual(c, c)

        # Test a class with an __eq__ and eq=False.
        @dataclass(eq=False)
        class C(object):
            x = field(int)
            def __eq__(self, other):
                return other == 10
        self.assertEqual(C(3), 10)

    def test_overwriting_eq(self):
        # If the class has __eq__, use it no matter the value of
        #  eq=.

        @dataclass
        class C(object):
            x = field(int)
            def __eq__(self, other):
                return other == 3
        self.assertEqual(C(1), 3)
        self.assertNotEqual(C(1), 1)

        @dataclass(eq=True)
        class C(object):
            x = field(int)
            def __eq__(self, other):
                return other == 4
        self.assertEqual(C(1), 4)
        self.assertNotEqual(C(1), 1)

        @dataclass(eq=False)
        class C(object):
            x = field(int)
            def __eq__(self, other):
                return other == 5
        self.assertEqual(C(1), 5)
        self.assertNotEqual(C(1), 1)