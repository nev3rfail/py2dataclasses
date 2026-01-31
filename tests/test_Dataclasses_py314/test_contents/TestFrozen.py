from ..common import *
class TestFrozen(unittest.TestCase):
    def test_frozen(self):
        @dataclass(frozen=True)
        class C:
            i: int

        c = C(10)
        self.assertEqual(c.i, 10)
        with self.assertRaises(FrozenInstanceError):
            c.i = 5
        self.assertEqual(c.i, 10)

    def test_frozen_empty(self):
        @dataclass(frozen=True)
        class C:
            pass

        c = C()
        self.assertNotHasAttr(c, 'i')
        with self.assertRaises(FrozenInstanceError):
            c.i = 5
        self.assertNotHasAttr(c, 'i')
        with self.assertRaises(FrozenInstanceError):
            del c.i

    def test_inherit(self):
        @dataclass(frozen=True)
        class C:
            i: int

        @dataclass(frozen=True)
        class D(C):
            j: int

        d = D(0, 10)
        with self.assertRaises(FrozenInstanceError):
            d.i = 5
        with self.assertRaises(FrozenInstanceError):
            d.j = 6
        self.assertEqual(d.i, 0)
        self.assertEqual(d.j, 10)

    def test_inherit_nonfrozen_from_empty_frozen(self):
        @dataclass(frozen=True)
        class C:
            pass

        with self.assertRaisesRegex(TypeError,
                                    'cannot inherit non-frozen dataclass from a frozen one'):
            @dataclass
            class D(C):
                j: int

    def test_inherit_frozen_mutliple_inheritance(self):
        @dataclass
        class NotFrozen:
            pass

        @dataclass(frozen=True)
        class Frozen:
            pass

        class NotDataclass:
            pass

        for bases in (
                (NotFrozen, Frozen),
                (Frozen, NotFrozen),
                (Frozen, NotDataclass),
                (NotDataclass, Frozen),
        ):
            with self.subTest(bases=bases):
                with self.assertRaisesRegex(
                        TypeError,
                        'cannot inherit non-frozen dataclass from a frozen one',
                ):
                    @dataclass
                    class NotFrozenChild(*bases):
                        pass

        for bases in (
                (NotFrozen, Frozen),
                (Frozen, NotFrozen),
                (NotFrozen, NotDataclass),
                (NotDataclass, NotFrozen),
        ):
            with self.subTest(bases=bases):
                with self.assertRaisesRegex(
                        TypeError,
                        'cannot inherit frozen dataclass from a non-frozen one',
                ):
                    @dataclass(frozen=True)
                    class FrozenChild(*bases):
                        pass

    def test_inherit_frozen_mutliple_inheritance_regular_mixins(self):
        @dataclass(frozen=True)
        class Frozen:
            pass

        class NotDataclass:
            pass

        class C1(Frozen, NotDataclass):
            pass
        self.assertEqual(C1.__mro__, (C1, Frozen, NotDataclass, object))

        class C2(NotDataclass, Frozen):
            pass
        self.assertEqual(C2.__mro__, (C2, NotDataclass, Frozen, object))

        @dataclass(frozen=True)
        class C3(Frozen, NotDataclass):
            pass
        self.assertEqual(C3.__mro__, (C3, Frozen, NotDataclass, object))

        @dataclass(frozen=True)
        class C4(NotDataclass, Frozen):
            pass
        self.assertEqual(C4.__mro__, (C4, NotDataclass, Frozen, object))

    def test_multiple_frozen_dataclasses_inheritance(self):
        @dataclass(frozen=True)
        class FrozenA:
            pass

        @dataclass(frozen=True)
        class FrozenB:
            pass

        class C1(FrozenA, FrozenB):
            pass
        self.assertEqual(C1.__mro__, (C1, FrozenA, FrozenB, object))

        class C2(FrozenB, FrozenA):
            pass
        self.assertEqual(C2.__mro__, (C2, FrozenB, FrozenA, object))

        @dataclass(frozen=True)
        class C3(FrozenA, FrozenB):
            pass
        self.assertEqual(C3.__mro__, (C3, FrozenA, FrozenB, object))

        @dataclass(frozen=True)
        class C4(FrozenB, FrozenA):
            pass
        self.assertEqual(C4.__mro__, (C4, FrozenB, FrozenA, object))

    def test_inherit_nonfrozen_from_empty(self):
        @dataclass
        class C:
            pass

        @dataclass
        class D(C):
            j: int

        d = D(3)
        self.assertEqual(d.j, 3)
        self.assertIsInstance(d, C)

    # Test both ways: with an intermediate normal (non-dataclass)
    #  class and without an intermediate class.
    def test_inherit_nonfrozen_from_frozen(self):
        for intermediate_class in [True, False]:
            with self.subTest(intermediate_class=intermediate_class):
                @dataclass(frozen=True)
                class C:
                    i: int

                if intermediate_class:
                    class I(C): pass
                else:
                    I = C

                with self.assertRaisesRegex(TypeError,
                                            'cannot inherit non-frozen dataclass from a frozen one'):
                    @dataclass
                    class D(I):
                        pass

    def test_inherit_frozen_from_nonfrozen(self):
        for intermediate_class in [True, False]:
            with self.subTest(intermediate_class=intermediate_class):
                @dataclass
                class C:
                    i: int

                if intermediate_class:
                    class I(C): pass
                else:
                    I = C

                with self.assertRaisesRegex(TypeError,
                                            'cannot inherit frozen dataclass from a non-frozen one'):
                    @dataclass(frozen=True)
                    class D(I):
                        pass

    def test_inherit_from_normal_class(self):
        for intermediate_class in [True, False]:
            with self.subTest(intermediate_class=intermediate_class):
                class C:
                    pass

                if intermediate_class:
                    class I(C): pass
                else:
                    I = C

                @dataclass(frozen=True)
                class D(I):
                    i: int

            d = D(10)
            with self.assertRaises(FrozenInstanceError):
                d.i = 5

    def test_non_frozen_normal_derived(self):
        # See bpo-32953.

        @dataclass(frozen=True)
        class D:
            x: int
            y: int = 10

        class S(D):
            pass

        s = S(3)
        self.assertEqual(s.x, 3)
        self.assertEqual(s.y, 10)
        s.cached = True

        # But can't change the frozen attributes.
        with self.assertRaises(FrozenInstanceError):
            s.x = 5
        with self.assertRaises(FrozenInstanceError):
            s.y = 5
        self.assertEqual(s.x, 3)
        self.assertEqual(s.y, 10)
        self.assertEqual(s.cached, True)

        with self.assertRaises(FrozenInstanceError):
            del s.x
        self.assertEqual(s.x, 3)
        with self.assertRaises(FrozenInstanceError):
            del s.y
        self.assertEqual(s.y, 10)
        del s.cached
        self.assertNotHasAttr(s, 'cached')
        with self.assertRaises(AttributeError) as cm:
            del s.cached
        self.assertNotIsInstance(cm.exception, FrozenInstanceError)

    def test_non_frozen_normal_derived_from_empty_frozen(self):
        @dataclass(frozen=True)
        class D:
            pass

        class S(D):
            pass

        s = S()
        self.assertNotHasAttr(s, 'x')
        s.x = 5
        self.assertEqual(s.x, 5)

        del s.x
        self.assertNotHasAttr(s, 'x')
        with self.assertRaises(AttributeError) as cm:
            del s.x
        self.assertNotIsInstance(cm.exception, FrozenInstanceError)

    def test_overwriting_frozen(self):
        # frozen uses __setattr__ and __delattr__.
        with self.assertRaisesRegex(TypeError,
                                    'Cannot overwrite attribute __setattr__'):
            @dataclass(frozen=True)
            class C:
                x: int
                def __setattr__(self):
                    pass

        with self.assertRaisesRegex(TypeError,
                                    'Cannot overwrite attribute __delattr__'):
            @dataclass(frozen=True)
            class C:
                x: int
                def __delattr__(self):
                    pass

        @dataclass(frozen=False)
        class C:
            x: int
            def __setattr__(self, name, value):
                self.__dict__['x'] = value * 2
        self.assertEqual(C(10).x, 20)

    def test_frozen_hash(self):
        @dataclass(frozen=True)
        class C:
            x: Any

        # If x is immutable, we can compute the hash.  No exception is
        # raised.
        hash(C(3))

        # If x is mutable, computing the hash is an error.
        with self.assertRaisesRegex(TypeError, 'unhashable type'):
            hash(C({}))

    def test_frozen_deepcopy_without_slots(self):
        # see: https://github.com/python/cpython/issues/89683
        @dataclass(frozen=True, slots=False)
        class C:
            s: str

        c = C('hello')
        self.assertEqual(deepcopy(c), c)

    def test_frozen_deepcopy_with_slots(self):
        # see: https://github.com/python/cpython/issues/89683
        with self.subTest('generated __slots__'):
            @dataclass(frozen=True, slots=True)
            class C:
                s: str

            c = C('hello')
            self.assertEqual(deepcopy(c), c)

        with self.subTest('user-defined __slots__ and no __{get,set}state__'):
            @dataclass(frozen=True, slots=False)
            class C:
                __slots__ = ('s',)
                s: str

            # with user-defined slots, __getstate__ and __setstate__ are not
            # automatically added, hence the error
            err = r"^cannot\ assign\ to\ field\ 's'$"
            self.assertRaisesRegex(FrozenInstanceError, err, deepcopy, C(''))

        with self.subTest('user-defined __slots__ and __{get,set}state__'):
            @dataclass(frozen=True, slots=False)
            class C:
                __slots__ = ('s',)
                __getstate__ = dataclasses._dataclass_getstate
                __setstate__ = dataclasses._dataclass_setstate

                s: str

            c = C('hello')
            self.assertEqual(deepcopy(c), c)
