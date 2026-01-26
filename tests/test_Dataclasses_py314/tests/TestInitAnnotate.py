from load_test import *
class TestInitAnnotate(unittest.TestCase):
    # Tests for the generated __annotate__ function for __init__
    # See: https://github.com/python/cpython/issues/137530

    def test_annotate_function(self):
        # No forward references
        @dataclass
        class A:
            a: int

        value_annos = annotationlib.get_annotations(A.__init__, format=annotationlib.Format.VALUE)
        forwardref_annos = annotationlib.get_annotations(A.__init__, format=annotationlib.Format.FORWARDREF)
        string_annos = annotationlib.get_annotations(A.__init__, format=annotationlib.Format.STRING)

        self.assertEqual(value_annos, {'a': int, 'return': None})
        self.assertEqual(forwardref_annos, {'a': int, 'return': None})
        self.assertEqual(string_annos, {'a': 'int', 'return': 'None'})

        self.assertTrue(getattr(A.__init__.__annotate__, "__generated_by_dataclasses__"))

    def test_annotate_function_forwardref(self):
        # With forward references
        @dataclass
        class B:
            b: undefined

        # VALUE annotations should raise while unresolvable
        with self.assertRaises(NameError):
            _ = annotationlib.get_annotations(B.__init__, format=annotationlib.Format.VALUE)

        forwardref_annos = annotationlib.get_annotations(B.__init__, format=annotationlib.Format.FORWARDREF)
        string_annos = annotationlib.get_annotations(B.__init__, format=annotationlib.Format.STRING)

        self.assertEqual(forwardref_annos, {'b': support.EqualToForwardRef('undefined', owner=B, is_class=True), 'return': None})
        self.assertEqual(string_annos, {'b': 'undefined', 'return': 'None'})

        # Now VALUE and FORWARDREF should resolve, STRING should be unchanged
        undefined = int

        value_annos = annotationlib.get_annotations(B.__init__, format=annotationlib.Format.VALUE)
        forwardref_annos = annotationlib.get_annotations(B.__init__, format=annotationlib.Format.FORWARDREF)
        string_annos = annotationlib.get_annotations(B.__init__, format=annotationlib.Format.STRING)

        self.assertEqual(value_annos, {'b': int, 'return': None})
        self.assertEqual(forwardref_annos, {'b': int, 'return': None})
        self.assertEqual(string_annos, {'b': 'undefined', 'return': 'None'})

    def test_annotate_function_init_false(self):
        # Check `init=False` attributes don't get into the annotations of the __init__ function
        @dataclass
        class C:
            c: str = field(init=False)

        self.assertEqual(annotationlib.get_annotations(C.__init__), {'return': None})

    def test_annotate_function_contains_forwardref(self):
        # Check string annotations on objects containing a ForwardRef
        @dataclass
        class D:
            d: list[undefined]

        with self.assertRaises(NameError):
            annotationlib.get_annotations(D.__init__)

        self.assertEqual(
            annotationlib.get_annotations(D.__init__, format=annotationlib.Format.FORWARDREF),
            {"d": list[support.EqualToForwardRef("undefined", is_class=True, owner=D)], "return": None}
        )

        self.assertEqual(
            annotationlib.get_annotations(D.__init__, format=annotationlib.Format.STRING),
            {"d": "list[undefined]", "return": "None"}
        )

        # Now test when it is defined
        undefined = str

        # VALUE should now resolve
        self.assertEqual(
            annotationlib.get_annotations(D.__init__),
            {"d": list[str], "return": None}
        )

        self.assertEqual(
            annotationlib.get_annotations(D.__init__, format=annotationlib.Format.FORWARDREF),
            {"d": list[str], "return": None}
        )

        self.assertEqual(
            annotationlib.get_annotations(D.__init__, format=annotationlib.Format.STRING),
            {"d": "list[undefined]", "return": "None"}
        )

    def test_annotate_function_not_replaced(self):
        # Check that __annotate__ is not replaced on non-generated __init__ functions
        @dataclass(slots=True)
        class E:
            x: str
            def __init__(self, x: int) -> None:
                self.x = x

        self.assertEqual(
            annotationlib.get_annotations(E.__init__), {"x": int, "return": None}
        )

        self.assertFalse(hasattr(E.__init__.__annotate__, "__generated_by_dataclasses__"))

    def test_slots_true_init_false(self):
        # Test that slots=True and init=False work together and
        #  that __annotate__ is not added to __init__.

        @dataclass(slots=True, init=False)
        class F:
            x: int

        f = F()
        f.x = 10
        self.assertEqual(f.x, 10)

        self.assertFalse(hasattr(F.__init__, "__annotate__"))

    def test_init_false_forwardref(self):
        # Test forward references in fields not required for __init__ annotations.

        # At the moment this raises a NameError for VALUE annotations even though the
        # undefined annotation is not required for the __init__ annotations.
        # Ideally this will be fixed but currently there is no good way to resolve this

        @dataclass
        class F:
            not_in_init: list[undefined] = field(init=False, default=None)
            in_init: int

        annos = annotationlib.get_annotations(F.__init__, format=annotationlib.Format.FORWARDREF)
        self.assertEqual(
            annos,
            {"in_init": int, "return": None},
        )

        with self.assertRaises(NameError):
            annos = annotationlib.get_annotations(F.__init__)  # NameError on not_in_init
