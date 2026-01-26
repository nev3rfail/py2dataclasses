from load_test import *

class TestFieldNoAnnotation(unittest.TestCase):

    def test_field_without_annotation(self):
        with self.assertRaisesRegexp(TypeError,
                                     "'f' is a field but has no type annotation"):
            @dataclass
            class TEST_NO_ANNOTATION(object):
                f = field()

            pass
    def test_field_without_annotation(self):
        with self.assertRaisesRegexp(TypeError,
                                     "'f' is a field but has no type annotation"):
            @dataclass
            class C(object):
                f = field()

    def test_field_without_annotation_but_annotation_in_base(self):
        @dataclass
        class B(object):
            f = field(int)

        with self.assertRaisesRegexp(TypeError,
                                     "'f' is a field but has no type annotation"):
            @dataclass
            class C(B):
                f = field()

    def test_field_without_annotation_but_annotation_in_base_not_dataclass(self):
        # Same test, but with the base class not a dataclass.
        class B(object):
            f = 0

        with self.assertRaisesRegexp(TypeError,
                                     "'f' is a field but has no type annotation"):
            @dataclass
            class C(B):
                f = field()
