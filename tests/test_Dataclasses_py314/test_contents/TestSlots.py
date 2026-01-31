from ..common import *
class TestSlots(unittest.TestCase):
    def test_simple(self):
        @dataclass
        class C:
            __slots__ = ('x',)
            x: Any

        # There was a bug where a variable in a slot was assumed to
        #  also have a default value (of type
        #  types.MemberDescriptorType).
        with self.assertRaisesRegex(TypeError,
                                    r"__init__\(\) missing 1 required positional argument: 'x'"):
            C()

        # We can create an instance, and assign to x.
        c = C(10)
        self.assertEqual(c.x, 10)
        c.x = 5
        self.assertEqual(c.x, 5)

        # We can't assign to anything else.
        with self.assertRaisesRegex(AttributeError, "'C' object has no attribute 'y'"):
            c.y = 5

    def test_derived_added_field(self):
        # See bpo-33100.
        @dataclass
        class Base:
            __slots__ = ('x',)
            x: Any

        @dataclass
        class Derived(Base):
            x: int
            y: int

        d = Derived(1, 2)
        self.assertEqual((d.x, d.y), (1, 2))

        # We can add a new field to the derived instance.
        d.z = 10

    def test_generated_slots(self):
        @dataclass(slots=True)
        class C:
            x: int
            y: int

        c = C(1, 2)
        self.assertEqual((c.x, c.y), (1, 2))

        c.x = 3
        c.y = 4
        self.assertEqual((c.x, c.y), (3, 4))

        with self.assertRaisesRegex(AttributeError, "'C' object has no attribute 'z'"):
            c.z = 5

    def test_add_slots_when_slots_exists(self):
        with self.assertRaisesRegex(TypeError, '^C already specifies __slots__$'):
            @dataclass(slots=True)
            class C:
                __slots__ = ('x',)
                x: int

    def test_generated_slots_value(self):

        class Root:
            __slots__ = {'x'}

        class Root2(Root):
            __slots__ = {'k': '...', 'j': ''}

        class Root3(Root2):
            __slots__ = ['h']

        class Root4(Root3):
            __slots__ = 'aa'

        @dataclass(slots=True)
        class Base(Root4):
            y: int
            j: str
            h: str

        self.assertEqual(Base.__slots__, ('y',))

        @dataclass(slots=True)
        class Derived(Base):
            aa: float
            x: str
            z: int
            k: str
            h: str

        self.assertEqual(Derived.__slots__, ('z',))

        @dataclass
        class AnotherDerived(Base):
            z: int

        self.assertNotIn('__slots__', AnotherDerived.__dict__)

    def test_slots_with_docs(self):
        class Root:
            __slots__ = {'x': 'x'}

        @dataclass(slots=True)
        class Base(Root):
            y1: int = field(doc='y1')
            y2: int

        self.assertEqual(Base.__slots__, {'y1': 'y1', 'y2': None})

        @dataclass(slots=True)
        class Child(Base):
            z1: int = field(doc='z1')
            z2: int

        self.assertEqual(Child.__slots__, {'z1': 'z1', 'z2': None})

    def test_cant_inherit_from_iterator_slots(self):

        class Root:
            __slots__ = iter(['a'])

        class Root2(Root):
            __slots__ = ('b', )

        with self.assertRaisesRegex(
                TypeError,
                "^Slots of 'Root' cannot be determined"
        ):
            @dataclass(slots=True)
            class C(Root2):
                x: int

    def test_returns_new_class(self):
        class A:
            x: int

        B = dataclass(A, slots=True)
        self.assertIsNot(A, B)

        self.assertNotHasAttr(A, "__slots__")
        self.assertHasAttr(B, "__slots__")

    # Can't be local to test_frozen_pickle.
    @dataclass(frozen=True, slots=True)
    class FrozenSlotsClass:
        foo: str
        bar: int

    @dataclass(frozen=True)
    class FrozenWithoutSlotsClass:
        foo: str
        bar: int

    def test_frozen_pickle(self):
        # bpo-43999

        self.assertEqual(self.FrozenSlotsClass.__slots__, ("foo", "bar"))
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            with self.subTest(proto=proto):
                obj = self.FrozenSlotsClass("a", 1)
                p = pickle.loads(pickle.dumps(obj, protocol=proto))
                self.assertIsNot(obj, p)
                self.assertEqual(obj, p)

                obj = self.FrozenWithoutSlotsClass("a", 1)
                p = pickle.loads(pickle.dumps(obj, protocol=proto))
                self.assertIsNot(obj, p)
                self.assertEqual(obj, p)

    @dataclass(frozen=True, slots=True)
    class FrozenSlotsGetStateClass:
        foo: str
        bar: int

        getstate_called: bool = field(default=False, compare=False)

        def __getstate__(self):
            object.__setattr__(self, 'getstate_called', True)
            return [self.foo, self.bar]

    @dataclass(frozen=True, slots=True)
    class FrozenSlotsSetStateClass:
        foo: str
        bar: int

        setstate_called: bool = field(default=False, compare=False)

        def __setstate__(self, state):
            object.__setattr__(self, 'setstate_called', True)
            object.__setattr__(self, 'foo', state[0])
            object.__setattr__(self, 'bar', state[1])

    @dataclass(frozen=True, slots=True)
    class FrozenSlotsAllStateClass:
        foo: str
        bar: int

        getstate_called: bool = field(default=False, compare=False)
        setstate_called: bool = field(default=False, compare=False)

        def __getstate__(self):
            object.__setattr__(self, 'getstate_called', True)
            return [self.foo, self.bar]

        def __setstate__(self, state):
            object.__setattr__(self, 'setstate_called', True)
            object.__setattr__(self, 'foo', state[0])
            object.__setattr__(self, 'bar', state[1])

    def test_frozen_slots_pickle_custom_state(self):
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            with self.subTest(proto=proto):
                obj = self.FrozenSlotsGetStateClass('a', 1)
                dumped = pickle.dumps(obj, protocol=proto)

                self.assertTrue(obj.getstate_called)
                self.assertEqual(obj, pickle.loads(dumped))

        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            with self.subTest(proto=proto):
                obj = self.FrozenSlotsSetStateClass('a', 1)
                obj2 = pickle.loads(pickle.dumps(obj, protocol=proto))

                self.assertTrue(obj2.setstate_called)
                self.assertEqual(obj, obj2)

        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            with self.subTest(proto=proto):
                obj = self.FrozenSlotsAllStateClass('a', 1)
                dumped = pickle.dumps(obj, protocol=proto)

                self.assertTrue(obj.getstate_called)

                obj2 = pickle.loads(dumped)
                self.assertTrue(obj2.setstate_called)
                self.assertEqual(obj, obj2)

    def test_slots_with_default_no_init(self):
        # Originally reported in bpo-44649.
        @dataclass(slots=True)
        class A:
            a: str
            b: str = field(default='b', init=False)

        obj = A("a")
        self.assertEqual(obj.a, 'a')
        self.assertEqual(obj.b, 'b')

    def test_slots_with_default_factory_no_init(self):
        # Originally reported in bpo-44649.
        @dataclass(slots=True)
        class A:
            a: str
            b: str = field(default_factory=lambda:'b', init=False)

        obj = A("a")
        self.assertEqual(obj.a, 'a')
        self.assertEqual(obj.b, 'b')

    def test_slots_no_weakref(self):
        @dataclass(slots=True)
        class A:
            # No weakref.
            pass

        self.assertNotIn("__weakref__", A.__slots__)
        a = A()
        with self.assertRaisesRegex(TypeError,
                                    "cannot create weak reference"):
            weakref.ref(a)
        with self.assertRaises(AttributeError):
            a.__weakref__

    def test_slots_weakref(self):
        @dataclass(slots=True, weakref_slot=True)
        class A:
            a: int

        self.assertIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)

        self.assertIs(a.__weakref__, a_ref)

    def test_slots_weakref_base_str(self):
        class Base:
            __slots__ = '__weakref__'

        @dataclass(slots=True)
        class A(Base):
            a: int

        # __weakref__ is in the base class, not A.  But an A is still weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        weakref.ref(a)

    def test_slots_weakref_base_tuple(self):
        # Same as test_slots_weakref_base, but use a tuple instead of a string
        # in the base class.
        class Base:
            __slots__ = ('__weakref__',)

        @dataclass(slots=True)
        class A(Base):
            a: int

        # __weakref__ is in the base class, not A.  But an A is still
        # weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        weakref.ref(a)

    def test_weakref_slot_without_slot(self):
        with self.assertRaisesRegex(TypeError,
                                    "weakref_slot is True but slots is False"):
            @dataclass(weakref_slot=True)
            class A:
                a: int

    def test_weakref_slot_make_dataclass(self):
        A = make_dataclass('A', [('a', int),], slots=True, weakref_slot=True)
        self.assertIn("__weakref__", A.__slots__)
        a = A(1)
        weakref.ref(a)

        # And make sure if raises if slots=True is not given.
        with self.assertRaisesRegex(TypeError,
                                    "weakref_slot is True but slots is False"):
            B = make_dataclass('B', [('a', int),], weakref_slot=True)

    def test_weakref_slot_subclass_weakref_slot(self):
        @dataclass(slots=True, weakref_slot=True)
        class Base:
            field: int

        # A *can* also specify weakref_slot=True if it wants to (gh-93521)
        @dataclass(slots=True, weakref_slot=True)
        class A(Base):
            ...

        # __weakref__ is in the base class, not A.  But an instance of A
        # is still weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)
        self.assertIs(a.__weakref__, a_ref)

    def test_weakref_slot_subclass_no_weakref_slot(self):
        @dataclass(slots=True, weakref_slot=True)
        class Base:
            field: int

        @dataclass(slots=True)
        class A(Base):
            ...

        # __weakref__ is in the base class, not A.  Even though A doesn't
        # specify weakref_slot, it should still be weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)
        self.assertIs(a.__weakref__, a_ref)

    def test_weakref_slot_normal_base_weakref_slot(self):
        class Base:
            __slots__ = ('__weakref__',)

        @dataclass(slots=True, weakref_slot=True)
        class A(Base):
            field: int

        # __weakref__ is in the base class, not A.  But an instance of
        # A is still weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)
        self.assertIs(a.__weakref__, a_ref)

    def test_dataclass_derived_weakref_slot(self):
        class A:
            pass

        @dataclass(slots=True, weakref_slot=True)
        class B(A):
            pass

        self.assertEqual(B.__slots__, ())
        B()

    def test_dataclass_derived_generic(self):
        T = typing.TypeVar('T')

        @dataclass(slots=True, weakref_slot=True)
        class A(typing.Generic[T]):
            pass
        self.assertEqual(A.__slots__, ('__weakref__',))
        self.assertTrue(A.__weakref__)
        A()

        @dataclass(slots=True, weakref_slot=True)
        class B[T2]:
            pass
        self.assertEqual(B.__slots__, ('__weakref__',))
        self.assertTrue(B.__weakref__)
        B()

    def test_dataclass_derived_generic_from_base(self):
        T = typing.TypeVar('T')

        class RawBase: ...

        @dataclass(slots=True, weakref_slot=True)
        class C1(typing.Generic[T], RawBase):
            pass
        self.assertEqual(C1.__slots__, ())
        self.assertTrue(C1.__weakref__)
        C1()
        @dataclass(slots=True, weakref_slot=True)
        class C2(RawBase, typing.Generic[T]):
            pass
        self.assertEqual(C2.__slots__, ())
        self.assertTrue(C2.__weakref__)
        C2()

        @dataclass(slots=True, weakref_slot=True)
        class D[T2](RawBase):
            pass
        self.assertEqual(D.__slots__, ())
        self.assertTrue(D.__weakref__)
        D()

    def test_dataclass_derived_generic_from_slotted_base(self):
        T = typing.TypeVar('T')

        class WithSlots:
            __slots__ = ('a', 'b')

        @dataclass(slots=True, weakref_slot=True)
        class E1(WithSlots, Generic[T]):
            pass
        self.assertEqual(E1.__slots__, ('__weakref__',))
        self.assertTrue(E1.__weakref__)
        E1()
        @dataclass(slots=True, weakref_slot=True)
        class E2(Generic[T], WithSlots):
            pass
        self.assertEqual(E2.__slots__, ('__weakref__',))
        self.assertTrue(E2.__weakref__)
        E2()

        @dataclass(slots=True, weakref_slot=True)
        class F[T2](WithSlots):
            pass
        self.assertEqual(F.__slots__, ('__weakref__',))
        self.assertTrue(F.__weakref__)
        F()

    def test_dataclass_derived_generic_from_slotted_base_with_weakref(self):
        T = typing.TypeVar('T')

        class WithWeakrefSlot:
            __slots__ = ('__weakref__',)

        @dataclass(slots=True, weakref_slot=True)
        class G1(WithWeakrefSlot, Generic[T]):
            pass
        self.assertEqual(G1.__slots__, ())
        self.assertTrue(G1.__weakref__)
        G1()
        @dataclass(slots=True, weakref_slot=True)
        class G2(Generic[T], WithWeakrefSlot):
            pass
        self.assertEqual(G2.__slots__, ())
        self.assertTrue(G2.__weakref__)
        G2()

        @dataclass(slots=True, weakref_slot=True)
        class H[T2](WithWeakrefSlot):
            pass
        self.assertEqual(H.__slots__, ())
        self.assertTrue(H.__weakref__)
        H()

    def test_dataclass_slot_dict(self):
        class WithDictSlot:
            __slots__ = ('__dict__',)

        @dataclass(slots=True)
        class A(WithDictSlot): ...

        self.assertEqual(A.__slots__, ())
        self.assertEqual(A().__dict__, {})
        A()

    @support.cpython_only
    def test_dataclass_slot_dict_ctype(self):
        # https://github.com/python/cpython/issues/123935
        # Skips test if `_testcapi` is not present:
        _testcapi = import_helper.import_module('_testcapi')

        @dataclass(slots=True)
        class HasDictOffset(_testcapi.HeapCTypeWithDict):
            __dict__: dict = {}
        self.assertNotEqual(_testcapi.HeapCTypeWithDict.__dictoffset__, 0)
        self.assertEqual(HasDictOffset.__slots__, ())

        @dataclass(slots=True)
        class DoesNotHaveDictOffset(_testcapi.HeapCTypeWithWeakref):
            __dict__: dict = {}
        self.assertEqual(_testcapi.HeapCTypeWithWeakref.__dictoffset__, 0)
        self.assertEqual(DoesNotHaveDictOffset.__slots__, ('__dict__',))

    @support.cpython_only
    def test_slots_with_wrong_init_subclass(self):
        # TODO: This test is for a kinda-buggy behavior.
        # Ideally, it should be fixed and `__init_subclass__`
        # should be fully supported in the future versions.
        # See https://github.com/python/cpython/issues/91126
        class WrongSuper:
            def __init_subclass__(cls, arg):
                pass

        with self.assertRaisesRegex(
                TypeError,
                "missing 1 required positional argument: 'arg'",
        ):
            @dataclass(slots=True)
            class WithWrongSuper(WrongSuper, arg=1):
                pass

        class CorrectSuper:
            args = []
            def __init_subclass__(cls, arg="default"):
                cls.args.append(arg)

        @dataclass(slots=True)
        class WithCorrectSuper(CorrectSuper):
            pass

        # __init_subclass__ is called twice: once for `WithCorrectSuper`
        # and once for `WithCorrectSuper__slots__` new class
        # that we create internally.
        self.assertEqual(CorrectSuper.args, ["default", "default"])

    def test_original_class_is_gced(self):
        # gh-135228: Make sure when we replace the class with slots=True, the original class
        # gets garbage collected.
        def make_simple():
            @dataclass(slots=True)
            class SlotsTest:
                pass

            return SlotsTest

        def make_with_annotations():
            @dataclass(slots=True)
            class SlotsTest:
                x: int

            return SlotsTest

        def make_with_annotations_and_method():
            @dataclass(slots=True)
            class SlotsTest:
                x: int

                def method(self) -> int:
                    return self.x

            return SlotsTest

        def make_with_forwardref():
            @dataclass(slots=True)
            class SlotsTest:
                x: undefined
                y: list[undefined]

            return SlotsTest

        for make in (make_simple, make_with_annotations, make_with_annotations_and_method, make_with_forwardref):
            with self.subTest(make=make):
                C = make()
                support.gc_collect()
                candidates = [cls for cls in object.__subclasses__() if cls.__name__ == 'SlotsTest'
                              and cls.__firstlineno__ == make.__code__.co_firstlineno + 1]
                self.assertEqual(candidates, [C])

