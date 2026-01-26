from load_test import *
class TestHash(unittest.TestCase):
    def test_unsafe_hash(self):
        @dataclass(unsafe_hash=True)
        class C:
            x: int
            y: str
        self.assertEqual(hash(C(1, 'foo')), hash((1, 'foo')))

    def test_hash_rules(self):
        def non_bool(value):
            # Map to something else that's True, but not a bool.
            if value is None:
                return None
            if value:
                return (3,)
            return 0

        def test(case, unsafe_hash, eq, frozen, with_hash, result):
            with self.subTest(case=case, unsafe_hash=unsafe_hash, eq=eq,
                              frozen=frozen):
                if result != 'exception':
                    if with_hash:
                        @dataclass(unsafe_hash=unsafe_hash, eq=eq, frozen=frozen)
                        class C:
                            def __hash__(self):
                                return 0
                    else:
                        @dataclass(unsafe_hash=unsafe_hash, eq=eq, frozen=frozen)
                        class C:
                            pass

                # See if the result matches what's expected.
                if result == 'fn':
                    # __hash__ contains the function we generated.
                    self.assertIn('__hash__', C.__dict__)
                    self.assertIsNotNone(C.__dict__['__hash__'])

                elif result == '':
                    # __hash__ is not present in our class.
                    if not with_hash:
                        self.assertNotIn('__hash__', C.__dict__)

                elif result == 'none':
                    # __hash__ is set to None.
                    self.assertIn('__hash__', C.__dict__)
                    self.assertIsNone(C.__dict__['__hash__'])

                elif result == 'exception':
                    # Creating the class should cause an exception.
                    #  This only happens with with_hash==True.
                    assert(with_hash)
                    with self.assertRaisesRegex(TypeError, 'Cannot overwrite attribute __hash__'):
                        @dataclass(unsafe_hash=unsafe_hash, eq=eq, frozen=frozen)
                        class C:
                            def __hash__(self):
                                return 0

                else:
                    assert False, f'unknown result {result!r}'

        # There are 8 cases of:
        #  unsafe_hash=True/False
        #  eq=True/False
        #  frozen=True/False
        # And for each of these, a different result if
        #  __hash__ is defined or not.
        for case, (unsafe_hash,  eq,    frozen, res_no_defined_hash, res_defined_hash) in enumerate([
            (False,        False, False,  '',                  ''),
            (False,        False, True,   '',                  ''),
            (False,        True,  False,  'none',              ''),
            (False,        True,  True,   'fn',                ''),
            (True,         False, False,  'fn',                'exception'),
            (True,         False, True,   'fn',                'exception'),
            (True,         True,  False,  'fn',                'exception'),
            (True,         True,  True,   'fn',                'exception'),
        ], 1):
            test(case, unsafe_hash, eq, frozen, False, res_no_defined_hash)
            test(case, unsafe_hash, eq, frozen, True,  res_defined_hash)

            # Test non-bool truth values, too.  This is just to
            #  make sure the data-driven table in the decorator
            #  handles non-bool values.
            test(case, non_bool(unsafe_hash), non_bool(eq), non_bool(frozen), False, res_no_defined_hash)
            test(case, non_bool(unsafe_hash), non_bool(eq), non_bool(frozen), True,  res_defined_hash)


    def test_eq_only(self):
        # If a class defines __eq__, __hash__ is automatically added
        #  and set to None.  This is normal Python behavior, not
        #  related to dataclasses.  Make sure we don't interfere with
        #  that (see bpo=32546).

        @dataclass
        class C:
            i: int
            def __eq__(self, other):
                return self.i == other.i
        self.assertEqual(C(1), C(1))
        self.assertNotEqual(C(1), C(4))

        # And make sure things work in this case if we specify
        #  unsafe_hash=True.
        @dataclass(unsafe_hash=True)
        class C:
            i: int
            def __eq__(self, other):
                return self.i == other.i
        self.assertEqual(C(1), C(1.0))
        self.assertEqual(hash(C(1)), hash(C(1.0)))

        # And check that the classes __eq__ is being used, despite
        #  specifying eq=True.
        @dataclass(unsafe_hash=True, eq=True)
        class C:
            i: int
            def __eq__(self, other):
                return self.i == 3 and self.i == other.i
        self.assertEqual(C(3), C(3))
        self.assertNotEqual(C(1), C(1))
        self.assertEqual(hash(C(1)), hash(C(1.0)))

    def test_0_field_hash(self):
        @dataclass(frozen=True)
        class C:
            pass
        self.assertEqual(hash(C()), hash(()))

        @dataclass(unsafe_hash=True)
        class C:
            pass
        self.assertEqual(hash(C()), hash(()))

    def test_1_field_hash(self):
        @dataclass(frozen=True)
        class C:
            x: int
        self.assertEqual(hash(C(4)), hash((4,)))
        self.assertEqual(hash(C(42)), hash((42,)))

        @dataclass(unsafe_hash=True)
        class C:
            x: int
        self.assertEqual(hash(C(4)), hash((4,)))
        self.assertEqual(hash(C(42)), hash((42,)))

    def test_hash_no_args(self):
        # Test dataclasses with no hash= argument.  This exists to
        #  make sure that if the @dataclass parameter name is changed
        #  or the non-default hashing behavior changes, the default
        #  hashability keeps working the same way.

        class Base:
            def __hash__(self):
                return 301

        # If frozen or eq is None, then use the default value (do not
        #  specify any value in the decorator).
        for frozen, eq,    base,   expected       in [
            (None,  None,  object, 'unhashable'),
            (None,  None,  Base,   'unhashable'),
            (None,  False, object, 'object'),
            (None,  False, Base,   'base'),
            (None,  True,  object, 'unhashable'),
            (None,  True,  Base,   'unhashable'),
            (False, None,  object, 'unhashable'),
            (False, None,  Base,   'unhashable'),
            (False, False, object, 'object'),
            (False, False, Base,   'base'),
            (False, True,  object, 'unhashable'),
            (False, True,  Base,   'unhashable'),
            (True,  None,  object, 'tuple'),
            (True,  None,  Base,   'tuple'),
            (True,  False, object, 'object'),
            (True,  False, Base,   'base'),
            (True,  True,  object, 'tuple'),
            (True,  True,  Base,   'tuple'),
        ]:

            with self.subTest(frozen=frozen, eq=eq, base=base, expected=expected):
                # First, create the class.
                if frozen is None and eq is None:
                    @dataclass
                    class C(base):
                        i: int
                elif frozen is None:
                    @dataclass(eq=eq)
                    class C(base):
                        i: int
                elif eq is None:
                    @dataclass(frozen=frozen)
                    class C(base):
                        i: int
                else:
                    @dataclass(frozen=frozen, eq=eq)
                    class C(base):
                        i: int

                # Now, make sure it hashes as expected.
                if expected == 'unhashable':
                    c = C(10)
                    with self.assertRaisesRegex(TypeError, 'unhashable type'):
                        hash(c)

                elif expected == 'base':
                    self.assertEqual(hash(C(10)), 301)

                elif expected == 'object':
                    # I'm not sure what test to use here.  object's
                    #  hash isn't based on id(), so calling hash()
                    #  won't tell us much.  So, just check the
                    #  function used is object's.
                    self.assertIs(C.__hash__, object.__hash__)

                elif expected == 'tuple':
                    self.assertEqual(hash(C(42)), hash((42,)))

                else:
                    assert False, f'unknown value for expected={expected!r}'
