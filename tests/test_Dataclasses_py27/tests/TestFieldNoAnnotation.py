from __future__ import print_function, absolute_import

from load_test import *

class TestFieldNoAnnotation(unittest.TestCase):
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
            # This is still an error: make sure we don't pick up the
            #  type annotation in the base class.
            @dataclass
            class C(B):
                f = field()

    def test_field_without_annotation_but_annotation_in_base_not_dataclass(self):
        # Same test, but with the base class not a dataclass.
        class B(object):
            pass

        with self.assertRaisesRegexp(TypeError,
                                    "'f' is a field but has no type annotation"):
            # This is still an error: make sure we don't pick up the
            #  type annotation in the base class.
            @dataclass
            class C(B):
                f = field()

