from load_test import *

class TestHash(unittest.TestCase):
    def test_unsafe_hash(self):
        @dataclass(unsafe_hash=True)
        class C(object):
            x = field(int)
            y = field(str)
        self.assertEqual(hash(C(1, 'foo')), hash((1, 'foo')))

    def test_hash_rules(self):
        def test(case, unsafe_hash, eq, frozen, with_hash, result):
            with self.subTest(case=case, unsafe_hash=unsafe_hash, eq=eq,
                              frozen=frozen):
                if result != 'exception':
                    if with_hash:
                        @dataclass(unsafe_hash=unsafe_hash, eq=eq, frozen=frozen)
                        class C(object):
                            def __hash__(self):
                                return 0
                    else:
                        @dataclass(unsafe_hash=unsafe_hash, eq=eq, frozen=frozen)
                        class C(object):
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
                    with self.assertRaisesRegexp(TypeError, 'Cannot overwrite attribute __hash__'):
                        @dataclass(unsafe_hash=unsafe_hash, eq=eq, frozen=frozen)
                        class C(object):
                            def __hash__(self):
                                return 0

        # There are 8 cases of:
        #  unsafe_hash=True/False
        #  eq=True/False
        #  frozen=True/False
        # And for each of these, a different result if
        #  __hash__ is defined or not.
        for case, (unsafe_hash,  eq,    frozen, res_no_defined_hash, res_defined_hash) in enumerate([
            (False,        False, False,  '',                  ''),
            (False,        False, True,   'fn',                'exception'),
            (False,        True,  False,  'none',              'exception'),
            (False,        True,  True,   'fn',                'exception'),
            (True,         False, False,  'fn',                'exception'),
            (True,         False, True,   'fn',                'exception'),
            (True,         True,  False,  'fn',                'exception'),
            (True,         True,  True,   'fn',                'exception'),
        ]):
            for with_hash in (False, True):
                if with_hash:
                    expected = res_defined_hash
                else:
                    expected = res_no_defined_hash
                test(case, unsafe_hash, eq, frozen, with_hash, expected)


    def test_hash_no_args(self):
        # Test dataclasses with no hash= argument.
        class Base(object):
            def __hash__(self):
                return 301

        # frozen=True should auto-generate __hash__
        @dataclass(frozen=True)
        class C(Base):
            i = field(int)

        self.assertEqual(hash(C(10)), hash((10,)))

    def test_0_field_hash(self):
        @dataclass(frozen=True)
        class C(object):
            pass
        self.assertEqual(hash(C()), hash(()))

        @dataclass(unsafe_hash=True)
        class C(object):
            pass
        self.assertEqual(hash(C()), hash(()))

    def test_1_field_hash(self):
        @dataclass(frozen=True)
        class C(object):
            x = field(int)
        self.assertEqual(hash(C(4)), hash((4,)))
        self.assertEqual(hash(C(42)), hash((42,)))

        @dataclass(unsafe_hash=True)
        class C(object):
            x = field(int)
        self.assertEqual(hash(C(4)), hash((4,)))
        self.assertEqual(hash(C(42)), hash((42,)))

    def test_eq_only(self):
        @dataclass
        class C(object):
            i = field(int)
            def __eq__(self, other):
                return self.i == other.i
        self.assertEqual(C(1), C(1))
        self.assertNotEqual(C(1), C(4))

        @dataclass(unsafe_hash=True)
        class C(object):
            i = field(int)
            def __eq__(self, other):
                return self.i == other.i
        self.assertEqual(C(1), C(1.0))
        self.assertEqual(hash(C(1)), hash(C(1.0)))