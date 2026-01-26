from load_test import *
class TestRepr(unittest.TestCase):
    def test_repr(self):
        @dataclass
        class B:
            x: int

        @dataclass
        class C(B):
            y: int = 10

        o = C(4)
        self.assertEqual(repr(o), 'TestRepr.test_repr.<locals>.C(x=4, y=10)')

        @dataclass
        class D(C):
            x: int = 20
        self.assertEqual(repr(D()), 'TestRepr.test_repr.<locals>.D(x=20, y=10)')

        @dataclass
        class C:
            @dataclass
            class D:
                i: int
            @dataclass
            class E:
                pass
        self.assertEqual(repr(C.D(0)), 'TestRepr.test_repr.<locals>.C.D(i=0)')
        self.assertEqual(repr(C.E()), 'TestRepr.test_repr.<locals>.C.E()')

    def test_no_repr(self):
        # Test a class with no __repr__ and repr=False.
        @dataclass(repr=False)
        class C:
            x: int
        self.assertIn(f'{__name__}.TestRepr.test_no_repr.<locals>.C object at',
                      repr(C(3)))

        # Test a class with a __repr__ and repr=False.
        @dataclass(repr=False)
        class C:
            x: int
            def __repr__(self):
                return 'C-class'
        self.assertEqual(repr(C(3)), 'C-class')

    def test_overwriting_repr(self):
        # If the class has __repr__, use it no matter the value of
        #  repr=.

        @dataclass
        class C:
            x: int
            def __repr__(self):
                return 'x'
        self.assertEqual(repr(C(0)), 'x')

        @dataclass(repr=True)
        class C:
            x: int
            def __repr__(self):
                return 'x'
        self.assertEqual(repr(C(0)), 'x')

        @dataclass(repr=False)
        class C:
            x: int
            def __repr__(self):
                return 'x'
        self.assertEqual(repr(C(0)), 'x')
