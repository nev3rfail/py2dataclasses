from load_test import *

class TestFrozen(unittest.TestCase):
    def test_inherit_frozen_mutliple_inheritance(self):
        @dataclass
        class NotFrozen(object):
            pass

        @dataclass(frozen=True)
        class Frozen(object):
            pass

        class NotDataclass(object):
            pass

        for bases in (
                (NotFrozen, Frozen),
                (Frozen, NotFrozen),
                (Frozen, NotDataclass),
                (NotDataclass, Frozen),
        ):
            with self.subTest(bases=bases):
                with self.assertRaisesRegexp(
                        TypeError,
                        'cannot inherit non-frozen dataclass from a frozen one',
                ):
                    @dataclass
                    class NotFrozenChild(bases):
                        pass

        for bases in (
                (NotFrozen, Frozen),
                (Frozen, NotFrozen),
                (NotFrozen, NotDataclass),
                (NotDataclass, NotFrozen),
        ):
            with self.subTest(bases=bases):
                with self.assertRaisesRegexp(
                        TypeError,
                        'cannot inherit frozen dataclass from a non-frozen one',
                ):
                    @dataclass(frozen=True)
                    class FrozenChild(bases):
                        pass

    def test_frozen_deepcopy_without_slots(self):
        @dataclass(frozen=True)
        class C(object):
            s = field(str)

        c = C('hello')
        self.assertEqual(copy.deepcopy(c), c)

    def test_frozen_deepcopy_with_slots(self):
        @dataclass(frozen=True, slots=True)
        class C(object):
            s = field(str)

        c = C('hello')
        self.assertEqual(copy.deepcopy(c), c)

    def test_multiple_frozen_dataclasses_inheritance(self):
        @dataclass(frozen=True)
        class FrozenA(object):
            pass

        @dataclass(frozen=True)
        class FrozenB(object):
            pass

        class C1(FrozenA, FrozenB):
            pass

        class C2(FrozenB, FrozenA):
            pass

        @dataclass(frozen=True)
        class C3(FrozenA, FrozenB):
            pass

        @dataclass(frozen=True)
        class C4(FrozenB, FrozenA):
            pass

    def test_inherit_frozen_mutliple_inheritance_regular_mixins(self):
        @dataclass(frozen=True)
        class Frozen(object):
            pass

        class NotDataclass(object):
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

    def test_frozen_empty(self):
        @dataclass(frozen=True)
        class C(object):
            pass

        c = C()
        self.assertFalse(hasattr(c, 'i'))
        with self.assertRaises(FrozenInstanceError):
            c.i = 5
        self.assertFalse(hasattr(c, 'i'))
        with self.assertRaises(FrozenInstanceError):
            del c.i

    def test_frozen(self):
        @dataclass(frozen=True)
        class C(object):
            i = field(int)

        c = C(10)
        self.assertEqual(c.i, 10)
        with self.assertRaises(FrozenInstanceError):
            c.i = 5
        self.assertEqual(c.i, 10)

    def test_frozen_hash(self):
        @dataclass(frozen=True)
        class C(object):
            x = field(object)

        # If x is immutable, we can compute the hash.
        hash(C(3))

        # If x is mutable, computing the hash is an error.
        with self.assertRaisesRegexp(TypeError, 'unhashable type'):
            hash(C({}))

    def test_inherit(self):
        @dataclass(frozen=True)
        class C(object):
            i = field(int)

        @dataclass(frozen=True)
        class D(C):
            j = field(int)

        d = D(0, 10)
        with self.assertRaises(FrozenInstanceError):
            d.i = 5
        with self.assertRaises(FrozenInstanceError):
            d.j = 6
        self.assertEqual(d.i, 0)
        self.assertEqual(d.j, 10)

    def test_inherit_nonfrozen_from_empty_frozen(self):
        @dataclass(frozen=True)
        class C(object):
            pass

        with self.assertRaisesRegexp(TypeError,
                                     'cannot inherit non-frozen dataclass from a frozen one'):
            @dataclass
            class D(C):
                j = field(int)

    def test_inherit_nonfrozen_from_empty(self):
        @dataclass
        class C(object):
            pass

        @dataclass
        class D(C):
            j = field(int)

        d = D(3)
        self.assertEqual(d.j, 3)
        self.assertIsInstance(d, C)

    def test_inherit_nonfrozen_from_frozen(self):
        @dataclass(frozen=True)
        class C(object):
            i = field(int)

        with self.assertRaisesRegexp(TypeError,
                                     'cannot inherit non-frozen dataclass from a frozen one'):
            @dataclass
            class D(C):
                pass

    def test_inherit_frozen_from_nonfrozen(self):
        @dataclass
        class C(object):
            i = field(int)

        with self.assertRaisesRegexp(TypeError,
                                     'cannot inherit frozen dataclass from a non-frozen one'):
            @dataclass(frozen=True)
            class D(C):
                pass

    def test_inherit_from_normal_class(self):
        class C(object):
            pass

        @dataclass(frozen=True)
        class D(C):
            i = field(int)

        d = D(10)
        with self.assertRaises(FrozenInstanceError):
            d.i = 5

    def test_non_frozen_normal_derived(self):
        @dataclass(frozen=True)
        class D(object):
            x = field(int)
            y = field(int, default=10)

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
        self.assertFalse(hasattr(s, 'cached'))
        with self.assertRaises(AttributeError) as cm:
            del s.cached
        self.assertNotIsInstance(cm.exception, FrozenInstanceError)

    def test_non_frozen_normal_derived_from_empty_frozen(self):
        @dataclass(frozen=True)
        class D(object):
            pass

        class S(D):
            pass

        s = S()
        self.assertFalse(hasattr(s, 'x'))
        s.x = 5
        self.assertEqual(s.x, 5)

        del s.x
        self.assertFalse(hasattr(s, 'x'))
        with self.assertRaises(AttributeError) as cm:
            del s.x
        self.assertNotIsInstance(cm.exception, FrozenInstanceError)

    def test_overwriting_frozen(self):
        # frozen uses __setattr__ and __delattr__.
        with self.assertRaisesRegexp(TypeError,
                                     'Cannot overwrite attribute __setattr__'):
            @dataclass(frozen=True)
            class C(object):
                x = field(int)
                def __setattr__(self):
                    pass

        with self.assertRaisesRegexp(TypeError,
                                     'Cannot overwrite attribute __delattr__'):
            @dataclass(frozen=True)
            class C(object):
                x = field(int)
                def __delattr__(self):
                    pass

        @dataclass(frozen=False)
        class C(object):
            x = field(int)
            def __setattr__(self, name, value):
                self.__dict__['x'] = value * 2
        self.assertEqual(C(10).x, 20)

