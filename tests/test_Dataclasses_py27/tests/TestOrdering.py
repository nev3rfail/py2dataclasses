from load_test import *

class TestOrdering(unittest.TestCase):
    def test_functools_total_ordering(self):
        # Test that functools.total_ordering works with this class.
        from functools import total_ordering
        @total_ordering
        @dataclass
        class C(object):
            x = field(int)
            def __lt__(self, other):
                # Perform the test "backward", just to make
                #  sure this is being called.
                return self.x >= other

        self.assertLess(C(0), -1)
        self.assertLessEqual(C(0), -1)
        self.assertGreater(C(0), 1)
        self.assertGreaterEqual(C(0), 1)

    def test_no_order(self):
        # Test that no ordering functions are added by default.
        @dataclass(order=False)
        class C(object):
            x = field(int)
        # Make sure no order methods are added.
        self.assertNotIn('__le__', C.__dict__)
        self.assertNotIn('__lt__', C.__dict__)
        self.assertNotIn('__ge__', C.__dict__)
        self.assertNotIn('__gt__', C.__dict__)

        # Test that __lt__ is still called
        @dataclass(order=False)
        class C(object):
            x = field(int)
            def __lt__(self, other):
                return False
        # Make sure other methods aren't added.
        self.assertNotIn('__le__', C.__dict__)
        self.assertNotIn('__ge__', C.__dict__)
        self.assertNotIn('__gt__', C.__dict__)

    def test_overwriting_order(self):
        with self.assertRaisesRegexp(TypeError,
                                     'Cannot overwrite attribute __lt__.*using functools.total_ordering'):
            @dataclass(order=True)
            class C(object):
                x = field(int)
                def __lt__(self):
                    pass

        with self.assertRaisesRegexp(TypeError,
                                     'Cannot overwrite attribute __le__.*using functools.total_ordering'):
            @dataclass(order=True)
            class C(object):
                x = field(int)
                def __le__(self):
                    pass

        with self.assertRaisesRegexp(TypeError,
                                     'Cannot overwrite attribute __gt__.*using functools.total_ordering'):
            @dataclass(order=True)
            class C(object):
                x = field(int)
                def __gt__(self):
                    pass

        with self.assertRaisesRegexp(TypeError,
                                     'Cannot overwrite attribute __ge__.*using functools.total_ordering'):
            @dataclass(order=True)
            class C(object):
                x = field(int)
                def __ge__(self):
                    pass
