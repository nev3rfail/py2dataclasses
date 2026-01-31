from __future__ import print_function, absolute_import

from ..common import *
class TestCase(unittest.TestCase):
    def assertNotHasAttr(self, obj, name):
        self.assertFalse(hasattr(obj, name),
                         '{0!r} has attribute {1!r}'.format(obj, name))

    def assertHasAttr(self, obj, name):
        self.assertTrue(hasattr(obj, name),
                        '{0!r} does not have attribute {1!r}'.format(obj, name))

    def test_no_fields(self):
        @dataclass
        class C(object):
            pass

        o = C()
        self.assertEqual(len(fields(C)), 0)

    def test_no_fields_but_member_variable(self):
        @dataclass
        class C(object):
            i = 0

        o = C()
        self.assertEqual(len(fields(C)), 0)

    def test_one_field_no_default(self):
        @dataclass
        class C(object):
            x = field(int)

        o = C(42)
        self.assertEqual(o.x, 42)

    def test_field_default_default_factory_error(self):
        msg = "cannot specify both default and default_factory"
        with self.assertRaisesRegexp(ValueError, msg):
            @dataclass
            class C(object):
                #__annotations__ = {'x': int}
                x = field(int, default=1, default_factory=int)

    def test_named_init_params(self):
        @dataclass
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int)

        o = C(x=32)
        self.assertEqual(o.x, 32)

    def test_two_fields_one_default(self):
        @dataclass
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int, 0)

        o = C(3)
        self.assertEqual((o.x, o.y), (3, 0))

        # Non-defaults following defaults.
        with self.assertRaisesRegexp(TypeError,
                                     "non-default argument 'y' follows "
                                     "default argument 'x'"):
            @dataclass
            class C(object):
                #__annotations__ = {'x': int, 'y': int}
                x = field(int, 0)
                y = field(int)

    def test_field_no_default(self):
        @dataclass
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int)

        self.assertEqual(C(5).x, 5)

        with self.assertRaisesRegexp(TypeError,
                                     r"__init__\(\) takes exactly 2 arguments \(1 given\)"):
            C()

    def test_field_default(self):
        default = object()
        @dataclass
        class C(object):
            #__annotations__ = {'x': object}
            x = field(object, default=default)

        self.assertIs(C.x, default)
        c = C(10)
        self.assertEqual(c.x, 10)

        # If we delete the instance attribute, we should then see the
        # class attribute.
        del c.x
        self.assertIs(c.x, default)

        self.assertIs(C().x, default)

    def test_not_in_repr(self):
        @dataclass
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int, repr=False)

        with self.assertRaises(TypeError):
            C()
        c = C(10)
        self.assertIn('C()', repr(c))

        @dataclass
        class CTEST(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int, repr=False)
            #c = field(int)
            y = field(int)
        c = CTEST(10, 20)
        self.assertIn('y=20', repr(c))

    def test_not_in_compare(self):
        @dataclass
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int, 0)
            y = field(compare=False, default=4)

        self.assertEqual(C(), C(0, 20))
        self.assertEqual(C(1, 10), C(1, 20))
        self.assertNotEqual(C(3), C(4, 10))
        self.assertNotEqual(C(3, 10), C(4, 10))

    def test_hash_field_rules(self):
        # Test all 6 cases of:
        #  hash=True/False/None
        #  compare=True/False
        for (hash_, compare, result) in [
            (True,  False, 'field'),
            (True,  True,  'field'),
            (False, False, 'absent'),
            (False, True,  'absent'),
            (None,  False, 'absent'),
            (None,  True,  'field'),
        ]:
            with self.subTest(hash=hash_, compare=compare):
                @dataclass(unsafe_hash=True)
                class C(object):
                    #__annotations__ = {'x': int}
                    x = field(_typ=int, compare=compare, hash=hash_, default=5)

                if result == 'field':
                    # __hash__ contains the field.
                    self.assertEqual(hash(C(5)), hash((5,)))
                elif result == 'absent':
                    # The field is not present in the hash.
                    self.assertEqual(hash(C(5)), hash(()))

    def test_init_false_no_default(self):
        # If init=False and no default value, then the field won't be
        # present in the instance.
        @dataclass
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int, init=False)

        self.assertNotIn('x', C().__dict__)

        @dataclass
        class CC(object):
            #__annotations__ = {'x': int, 'y': int, 'z': int, 't': int}
            x = field(int)
            #ss0 = sys._getframe(0)
            #ss = sys._getframe(1)
            y = field(int, 0)
            z = field(int, init=False)
            t = field(int, 10)
        #a = C(0)

        #bb = a.z
        self.assertNotIn('z', CC(0).__dict__)
        self.assertEqual(vars(CC(5)), {'t': 10, 'x': 5, 'y': 0})

    def test_class_marker(self):
        @dataclass
        class C(object):

            #__annotations__ = {'x': int, 'y': str, 'z': str}
            x = field(int)
            y = field(str,default=None, init=False)
            z = field(str,repr=False)
        #a = C(1, 2)
        #aaaa = a.x
        the_fields = fields(C)
        # the_fields is a tuple of 3 items
        self.assertIsInstance(the_fields, tuple)
        for f in the_fields:
            try:
                from py2dataclasses import _oneshot
                container = [Field, _oneshot]
            except:
                container = [Field]
            self.assertIn(type(f), container)
            self.assertIn(f.name, C.__annotations__)

        self.assertEqual(len(the_fields), 3)

        self.assertEqual(the_fields[0].name, 'x')
        self.assertEqual(the_fields[0].type, int)
        self.assertNotHasAttr(C, 'x')
        self.assertTrue(the_fields[0].init)
        self.assertTrue(the_fields[0].repr)
        self.assertEqual(the_fields[1].name, 'y')
        self.assertEqual(the_fields[1].type, str)
        self.assertIsNone(getattr(C, 'y'))
        self.assertFalse(the_fields[1].init)
        self.assertTrue(the_fields[1].repr)
        self.assertEqual(the_fields[2].name, 'z')
        self.assertEqual(the_fields[2].type, str)
        self.assertNotHasAttr(C, 'z')
        self.assertTrue(the_fields[2].init)
        self.assertFalse(the_fields[2].repr)
        #pew = C.z
    # def test_field_order(self):
    #     @dataclass
    #     class B:
    #         a: str = 'B:a'
    #         b: str = 'B:b'
    #         c: str = 'B:c'
    #
    #     @dataclass
    #     class C(B):
    #         b: str = 'C:b'
    #
    #     self.assertEqual([(f.name, f.default) for f in fields(C)],
    #                      [('a', 'B:a'),
    #                       ('b', 'C:b'),
    #                       ('c', 'B:c')])
    #
    #     @dataclass
    #     class D(B):
    #         c: str = 'D:c'
    #
    #     self.assertEqual([(f.name, f.default) for f in fields(D)],
    #                      [('a', 'B:a'),
    #                       ('b', 'B:b'),
    #                       ('c', 'D:c')])
    #
    #     @dataclass
    #     class E(D):
    #         a: str = 'E:a'
    #         d: str = 'E:d'
    #
    #     self.assertEqual([(f.name, f.default) for f in fields(E)],
    #                      [('a', 'E:a'),
    #                       ('b', 'B:b'),
    #                       ('c', 'D:c'),
    #                       ('d', 'E:d')])
    def test_field_order(self):
        @dataclass
        class B(object):
            #__annotations__ = OrderedDict((('a', str), ('b', str), ('c', str)))
            a = field(str, 'B:a')
            b = field(str, 'B:b')
            c = field(str, 'B:c')

        @dataclass
        class C(B):
            ##__annotations__ = {'b': str}
            b = field(str, 'C:b')

        self.assertEqual([(f.name, f.default) for f in fields(C)],
                         [('a', 'B:a'),
                          ('b', 'C:b'),
                          ('c', 'B:c')])

    def test_disallowed_mutable_defaults(self):
        # For the known types, don't allow mutable default values.
        for typ, empty, non_empty in [(list, [], [1]),
                                      (dict, {}, {0: 1}),
                                      (set, set(), set([1]))]:
            with self.subTest(typ=typ):
                # Can't use a zero-length value.
                with self.assertRaisesRegexp(ValueError,
                                             'mutable default .* for field '
                                             'x is not allowed'):
                    @dataclass
                    class Point(object):
                        #__annotations__ = {'x': typ}
                        x = field(typ, empty)

    def test_no_options(self):
        # Call with dataclass().
        @dataclass()
        class C(object):
            x = field(int)

        self.assertEqual(C(42).x, 42)

    def test_not_tuple(self):
        # Make sure we can't be compared to a tuple.
        @dataclass
        class Point(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int)

        self.assertNotEqual(Point(1, 2), (1, 2))

        # And that we can't compare to another unrelated dataclass.
        @dataclass
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int)

        self.assertNotEqual(Point(1, 3), C(1, 3))

    def test_post_init(self):
        # Just make sure it gets called
        @dataclass
        class C(object):
            def __post_init__(self):
                raise CustomError()
        with self.assertRaises(CustomError):
            C()

        @dataclass
        class C(object):
            #__annotations__ = {'i': int}
            i = field(int, 10)

            def __post_init__(self):
                if self.i == 10:
                    raise CustomError()
        with self.assertRaises(CustomError):
            C()
        # post-init gets called, but doesn't raise.
        C(5)

    def test_helper_fields_with_class_instance(self):
        # Check that we can call fields() on either a class or instance,
        # and get back the same thing.
        @dataclass
        class C(object):
            x = field(int)
            y = field(int)
        self.assertEqual(fields(C), fields(C(0, 0.0)))

    def test_helper_fields_exception(self):
        # Check that TypeError is raised if not passed a dataclass or instance.
        with self.assertRaisesRegexp(TypeError, 'dataclass type or instance'):
            fields(0)

        class C(object):
            pass
        with self.assertRaisesRegexp(TypeError, 'dataclass type or instance'):
            fields(C)
        with self.assertRaisesRegexp(TypeError, 'dataclass type or instance'):
            fields(C())

    def test_helper_asdict(self):
        # Basic tests for asdict(), it should return a new dictionary.
        #@dataclass
        @dataclass
        class C(object):
            x = field(int)
            y = field(int)
        c = C(1, 2)

        self.assertEqual(asdict(c), OrderedDict((('x', 1), ('y', 2))))
        self.assertEqual(asdict(c), asdict(c))
        self.assertIsNot(asdict(c), asdict(c))
        c.x = 42
        self.assertEqual(asdict(c), OrderedDict((('x', 42), ('y', 2))))
        self.assertIs(type(asdict(c, dict)), dict)

    def test_helper_asdict_raises_on_classes(self):
        # asdict() should raise on a class object.
        @dataclass
        class C(object):
            x = field(int)
            y = field(int)

        with self.assertRaisesRegexp(TypeError, 'dataclass instance'):
            asdict(C)
        with self.assertRaisesRegexp(TypeError, 'dataclass instance'):
            asdict(int)

    def test_helper_asdict_nested(self):
        @dataclass
        class UserId(object):
            #__annotations__ = {'token': int, 'group': int}
            token = field(int)
            group = field(int)

        @dataclass
        class User(object):
            #__annotations__ = {'name': str, 'id': UserId}
            name = field(str)
            id =  field(UserId)

        u = User('Joe', UserId(123, 1))
        d = asdict(u)
        self.assertEqual(d, {'name': 'Joe', 'id': {'token': 123, 'group': 1}})
        self.assertIsNot(asdict(u), asdict(u))
        u.id.group = 2
        self.assertEqual(asdict(u), {'name': 'Joe',
                                     'id': {'token': 123, 'group': 2}})

    def test_helper_astuple(self):
        # Basic tests for astuple(), it should return a new tuple.
        @dataclass
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(_typ=int)
            y = field(int, 0)

        c = C(1)

        self.assertEqual(astuple(c), (1, 0))
        self.assertEqual(astuple(c), astuple(c))
        self.assertIsNot(astuple(c), astuple(c))
        c.y = 42
        self.assertEqual(astuple(c), (1, 42))
        self.assertIs(type(astuple(c)), tuple)

    def test_helper_astuple_raises_on_classes(self):
        # astuple() should raise on a class object.
        @dataclass
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(_typ=int)
            y = field(_typ=int)

        with self.assertRaisesRegexp(TypeError, 'dataclass instance'):
            astuple(C)
        with self.assertRaisesRegexp(TypeError, 'dataclass instance'):
            astuple(int)

    def test_helper_astuple_nested(self):
        @dataclass
        class UserId(object):
            #__annotations__ = {'token': int, 'group': int}
            token = field(int)
            group = field(int)

        @dataclass
        class User(object):
            name = field(str)
            id = field(UserId)


        u = User('Joe', UserId(123, 1))
        pew = u.name
        t = astuple(u)
        self.assertEqual(t, ('Joe', (123, 1)))
        self.assertIsNot(astuple(u), astuple(u))
        u.id.group = 2
        self.assertEqual(astuple(u), ('Joe', (123, 2)))

    def test_dynamic_class_creation(self):
        cls_dict = {'__annotations__': OrderedDict((("x",int), ("y",int)))}

        # Create the class.
        cls = type('C', (object,), cls_dict)

        # Make it a dataclass.
        cls1 = dataclass(cls)

        self.assertEqual(cls1, cls)
        self.assertEqual(asdict(cls(1, 2)), {'x': 1, 'y': 2})

    def test_dynamic_class_creation_using_field(self):
        cls_dict = {
            '__annotations__': OrderedDict((("x",int), ("y",int))),
            'y': field( int, default=5),
        }

        # Create the class.
        cls = type('C', (object,), cls_dict)

        # Make it a dataclass.
        cls1 = dataclass(cls)

        self.assertEqual(cls1, cls)
        self.assertEqual(asdict(cls1(1)), {'x': 1, 'y': 5})

    def test_is_dataclass(self):
        class NotDataClass(object):
            pass

        self.assertFalse(is_dataclass(0))
        self.assertFalse(is_dataclass(int))
        self.assertFalse(is_dataclass(NotDataClass))
        self.assertFalse(is_dataclass(NotDataClass()))

        @dataclass
        class C(object):
            x = field(int)
        @dataclass
        class D(object):
            d = field(C)
            e = field(int)
            #__annotations__ = {'d': C, 'e': int}

        c = C(10)
        d = D(c, 4)

        self.assertTrue(is_dataclass(C))
        self.assertTrue(is_dataclass(c))
        self.assertFalse(is_dataclass(c.x))
        self.assertTrue(is_dataclass(d.d))
        self.assertFalse(is_dataclass(d.e))

    def test_0_field_compare(self):
        # Ensure that order=False is the default.
        @dataclass
        class C0(object):
            pass

        @dataclass(order=False)
        class C1(object):
            pass

        for cls in [C0, C1]:
            with self.subTest(cls=cls):
                self.assertEqual(cls(), cls())
                for idx, fn in enumerate([lambda a, b: a < b,
                                          lambda a, b: a <= b,
                                          lambda a, b: a > b,
                                          lambda a, b: a >= b]):
                    with self.subTest(idx=idx):
                        with self.assertRaisesRegexp(TypeError,
                                                     "not supported between instances"):
                            fn(cls(), cls())

    def test_simple_compare(self):
        # Ensure that order=False is the default.
        @dataclass
        class C0(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int)

        @dataclass(order=False)
        class C1(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int)

        for cls in [C0, C1]:
            with self.subTest(cls=cls):
                self.assertEqual(cls(0, 0), cls(0, 0))
                self.assertEqual(cls(1, 2), cls(1, 2))
                self.assertNotEqual(cls(1, 0), cls(0, 0))
                self.assertNotEqual(cls(1, 0), cls(1, 1))

        @dataclass(order=True)
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int)

        self.assertTrue(C(0, 0) == C(0, 0))
        self.assertTrue(C(0, 0) <= C(0, 0))
        self.assertTrue(C(0, 0) >= C(0, 0))
        self.assertTrue(C(0, 0) < C(0, 1))
        self.assertTrue(C(0, 1) < C(1, 0))
    #
    # def test_eq_order(self):
    #     # Test combining eq and order.
    #     for (eq, order, result) in [
    #         (False, False, 'neither'),
    #         (False, True,  'exception'),
    #         (True,  False, 'eq_only'),
    #         (True,  True,  'both'),
    #     ]:
    #         with self.subTest(eq=eq, order=order):
    #             if result == 'exception':
    #                 with self.assertRaisesRegexp(ValueError, 'eq must be true if order is true'):
    #                     @dataclass(eq=eq, order=order)
    #                     class C(object):
    #                         pass
    #             else:
    #                 @dataclass(eq=eq, order=order)
    #                 class C(object):
    #                     pass
    #
    #                 if result == 'neither':
    #                     self.assertNotIn('__eq__', C.__dict__)
    #                     self.assertNotIn('__lt__', C.__dict__)
    #                 elif result == 'both':
    #                     self.assertIn('__eq__', C.__dict__)
    #                     self.assertIn('__lt__', C.__dict__)
    #                 elif result == 'eq_only':
    #                     self.assertIn('__eq__', C.__dict__)
    #                     self.assertNotIn('__lt__', C.__dict__)


    def test_default_factory(self):
        # Test a factory that returns a new list.
        @dataclass
        class C(object):
            x = field(int)
            y = field(list, default_factory=list)

        c0 = C(3)
        c1 = C(3)
        self.assertEqual(c0.x, 3)
        self.assertEqual(c0.y, [])
        self.assertEqual(c0, c1)
        self.assertIsNot(c0.y, c1.y)
        self.assertEqual(astuple(C(5, [1])), (5, [1]))

    def test_missing_default(self):
        # Test that MISSING works the same as a default not being specified.
        @dataclass
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int, default=MISSING)

        with self.assertRaisesRegexp(TypeError,
                                     r"__init__\(\) takes exactly 2 arguments \(1 given\)"):
            C()
        self.assertNotIn('x', C.__dict__)

    def test_missing_default_factory(self):
        # Test that MISSING works the same as a default factory not being specified.
        @dataclass
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int, default_factory=MISSING)

        with self.assertRaisesRegexp(TypeError,
                                     r"__init__\(\) takes exactly 2 arguments \(1 given\)"):
            C()
        self.assertNotIn('x', C.__dict__)

    def test_field_repr(self):
        int_field = field(default=1, init=True, repr=False)
        int_field.name = "id"
        repr_output = repr(int_field)

        expected_output = "Field(name='id',type=None," \
                          "default=1,default_factory=%r," \
                          "init=True,repr=False,hash=None," \
                          "compare=True,metadata=mappingproxy({})," \
                          "kw_only=%r," \
                          "_field_type=None)" % (MISSING, MISSING)
        expected_output = "(name=('id'),default=1,init=True,compare=True" \
                          "".format(int_field.__class__.__name__)
        self.assertIn( expected_output, repr_output)
    @unittest.skip("Do not want")
    def test_field_recursive_repr(self):
        rec_field = field()
        rec_field.type = rec_field
        rec_field.name = "id"
        repr_output = repr(rec_field)

        self.assertIn(",type=...,", repr_output)
    class GC(object):
        pass
    def test_recursive_annotation(self):
        class C(object):
            pass

        @dataclass
        class RECURSIVE(object):
            GC = field(TestCase.GC)
        _locals = locals()
        @dataclass
        class D(object):
            C = field(_locals["C"])

        self.assertIn("<C>", repr(D.__dataclass_fields__["C"]))

    def test_dataclass_params_repr(self):
        # Even though this is testing an internal implementation detail,
        # it's testing a feature we want to make sure is correctly implemented
        # for the sake of dataclasses itself
        @dataclass(slots=True, frozen=True)
        class Some(object):
            pass

        repr_output = repr(Some.__dataclass_params__)
        expected_output = "_DataclassParams(init=True,repr=True," \
                          "eq=True,order=False,unsafe_hash=False,frozen=True," \
                          "match_args=True,kw_only=False," \
                          "slots=True,weakref_slot=False)"
        self.assertEqual(repr_output, expected_output)

    def test_dataclass_params_signature(self):
        # Even though this is testing an internal implementation detail,
        # it's testing a feature we want to make sure is correctly implemented
        # for the sake of dataclasses itself
        @dataclass
        class Some(object):
            pass

        import funcsigs
        for param in funcsigs.signature(dataclass).parameters:
            if param == 'cls':
                continue
            self.assertTrue(hasattr(Some.__dataclass_params__, param), msg=param)

    def test_overwrite_hash(self):
        # Test that declaring this class isn't an error.  It should
        #  use the user-provided __hash__.
        @dataclass(frozen=True)
        class C(object):
            x = field(int)
            def __hash__(self):
                return 301
        self.assertEqual(hash(C(100)), 301)

        # Test that declaring this class isn't an error.  It should
        #  use the generated __hash__.
        @dataclass(frozen=True)
        class C(object):
            x = field(int)
            def __eq__(self, other):
                return False
        self.assertEqual(hash(C(100)), hash((100,)))

        # But this one should generate an exception, because with
        #  unsafe_hash=True, it's an error to have a __hash__ defined.
        with self.assertRaisesRegexp(TypeError,
                                     'Cannot overwrite attribute __hash__'):
            @dataclass(unsafe_hash=True)
            class C(object):
                def __hash__(self):
                    pass

        # Creating this class should not generate an exception,
        #  because even though __hash__ exists before @dataclass is
        #  called, (due to __eq__ being defined), since it's None
        #  that's okay.
        @dataclass(unsafe_hash=True)
        class C(object):
            x = field(int)
            def __eq__(self):
                pass
        # The generated hash function works as we'd expect.
        self.assertEqual(hash(C(10)), hash((10,)))

        # Creating this class should generate an exception, because
        #  __hash__ exists and is not None, which it would be if it
        #  had been auto-generated due to __eq__ being defined.
        with self.assertRaisesRegexp(TypeError,
                                     'Cannot overwrite attribute __hash__'):
            @dataclass(unsafe_hash=True)
            class C(object):
                x = field(int)
                def __eq__(self):
                    pass
                def __hash__(self):
                    pass

    def test_overwrite_fields_in_derived_class(self):
        # Note that x from C1 replaces x in Base, but the order remains
        #  the same as defined in Base.
        from typing import Any
        @dataclass
        class Base(object):
            x = field(Any, 15.0)
            y = field(int, 0)

        @dataclass
        class C1(Base):
            z = field(int, 10)
            x = field(int, 15)

        o = Base()
        self.assertIn('Base(x=15.0, y=0)', repr(o))

        o = C1()
        self.assertIn('C1(x=15, y=0, z=10)', repr(o))

        o = C1(x=5)
        self.assertIn('C1(x=5, y=0, z=10)', repr(o))

    def test_field_named_self(self):
        @dataclass
        class C(object):
            self = field(str)
        c=C('foo')
        self.assertEqual(c.self, 'foo')

        # Make sure the first parameter is not named 'self'.
        import funcsigs
        sig = funcsigs.signature(C.__init__)
        first = next(iter(sig.parameters))
        self.assertNotEqual('self', first)

        # But we do use 'self' if no field named self.
        @dataclass
        class C(object):
            selfx = field(str)

        # Make sure the first parameter is named 'self'.
        sig = funcsigs.signature(C.__init__)
        first = next(iter(sig.parameters))
        self.assertEqual('self', first)

    def test_field_named_object(self):
        @dataclass
        class C(object):
            object = field(str)
        c = C('foo')
        self.assertEqual(c.object, 'foo')

    def test_field_named_object_frozen(self):
        @dataclass(frozen=True)
        class C(object):
            object = field(str)
        c = C('foo')
        self.assertEqual(c.object, 'foo')

    def test_field_named_BUILTINS_frozen(self):
        # gh-96151
        @dataclass(frozen=True)
        class C(object):
            BUILTINS = field(int)
        c = C(5)
        self.assertEqual(c.BUILTINS, 5)

    def test_field_with_special_single_underscore_names(self):
        # gh-98886

        @dataclass
        class X(object):
            x = field(int, default_factory=lambda: 111)
            _dflt_x = field(int, default_factory=lambda: 222)

        X()

        @dataclass
        class Y(object):
            y = field(int, default_factory=lambda: 111)
            _HAS_DEFAULT_FACTORY = 222

        assert Y(y=222).y == 222

    def test_field_named_like_builtin(self):
        # Attribute names can shadow built-in names
        # since code generation is used.
        # Ensure that this is not happening.
        #import __builtins__
        exclusions = {'None', 'True', 'False'}
        builtins_names = sorted(
            b for b in __builtins__.keys()
            if not b.startswith('__') and b not in exclusions
        )
        attributes = [(name, str) for name in builtins_names]
        C = make_dataclass('C', attributes)

        c = C(*[name for name in builtins_names])

        for name in builtins_names:
            self.assertEqual(getattr(c, name), name)

    def test_field_named_like_builtin_frozen(self):
        # Attribute names can shadow built-in names
        # since code generation is used.
        # Ensure that this is not happening
        # for frozen data classes.
        #import builtins
        exclusions = {'None', 'True', 'False'}
        builtins_names = sorted(
            b for b in __builtins__.keys()
            if not b.startswith('__') and b not in exclusions
        )
        attributes = [(name, str) for name in builtins_names]
        C = make_dataclass('C', attributes, frozen=True)

        c = C(*[name for name in builtins_names])

        for name in builtins_names:
            self.assertEqual(getattr(c, name), name)

    def test_1_field_compare(self):
        # Ensure that order=False is the default.
        @dataclass
        class C0(object):
            x = field(int)

        @dataclass(order=False)
        class C1(object):
            x = field(int)

        for cls in [C0, C1]:
            with self.subTest(cls=cls):
                self.assertEqual(cls(1), cls(1))
                self.assertNotEqual(cls(0), cls(1))
                for idx, fn in enumerate([lambda a, b: a < b,
                                          lambda a, b: a <= b,
                                          lambda a, b: a > b,
                                          lambda a, b: a >= b]):
                    with self.subTest(idx=idx):
                        with self.assertRaisesRegexp(TypeError,
                                                     "not supported between instances"):
                            fn(cls(0), cls(0))

        @dataclass(order=True)
        class C(object):
            x = field(int)
        self.assertTrue(C(0) < C(1))
        self.assertTrue(C(0) <= C(1))
        self.assertTrue(C(1) <= C(1))
        self.assertTrue(C(1) > C(0))
        self.assertTrue(C(1) >= C(0))
        self.assertTrue(C(1) >= C(1))

    def test_compare_subclasses(self):
        # Comparisons fail for subclasses, even if no fields
        #  are added.
        @dataclass
        class B(object):
            i = field(int)

        @dataclass
        class C(B):
            pass

        for idx, (fn, expected) in enumerate([(lambda a, b: a == b, False),
                                              (lambda a, b: a != b, True)]):
            with self.subTest(idx=idx):
                self.assertEqual(fn(B(0), C(0)), expected)

        for idx, fn in enumerate([lambda a, b: a < b,
                                  lambda a, b: a <= b,
                                  lambda a, b: a > b,
                                  lambda a, b: a >= b]):
            with self.subTest(idx=idx):
                with self.assertRaisesRegexp(TypeError,
                                             "not supported between instances of B and C"):
                    fn(B(0), C(0))
    @unittest.skip("We have __lt__ and __gt__ everywhere to trigger a proper exception")
    def test_eq_order(self):
        # Test combining eq and order.
        for (eq,    order, result   ) in [
            (False, False, 'neither'),
            (False, True,  'exception'),
            (True,  False, 'eq_only'),
            (True,  True,  'both'),
        ]:
            with self.subTest(eq=eq, order=order):
                if result == 'exception':
                    with self.assertRaisesRegexp(ValueError, 'eq must be true if order is true'):
                        @dataclass(eq=eq, order=order)
                        class C(object):
                            pass
                else:
                    @dataclass(eq=eq, order=order)
                    class C(object):
                        pass

                    if result == 'neither':
                        self.assertNotIn('__eq__', C.__dict__)
                        self.assertNotIn('__lt__', C.__dict__)
                        self.assertNotIn('__le__', C.__dict__)
                        self.assertNotIn('__gt__', C.__dict__)
                        self.assertNotIn('__ge__', C.__dict__)
                    elif result == 'both':
                        self.assertIn('__eq__', C.__dict__)
                        self.assertIn('__lt__', C.__dict__)
                        self.assertIn('__le__', C.__dict__)
                        self.assertIn('__gt__', C.__dict__)
                        self.assertIn('__ge__', C.__dict__)
                    elif result == 'eq_only':
                        self.assertIn('__eq__', C.__dict__)
                        self.assertNotIn('__lt__', C.__dict__)
                        self.assertNotIn('__le__', C.__dict__)
                        self.assertNotIn('__gt__', C.__dict__)
                        self.assertNotIn('__ge__', C.__dict__)
                    else:
                        assert False, 'unknown result %r' % result

    def test_class_attrs(self):
        # We only have a class attribute if a default value is
        #  specified, either directly or via a field with a default.
        default = object()
        @dataclass
        class C(object):
            x = field(int)
            y = field(int, repr=False)
            z = field(object, default=default)
            t = field(int, default=100)

        self.assertFalse(hasattr(C, 'x'))
        self.assertFalse(hasattr(C, 'y'))
        self.assertIs   (C.z, default)
        self.assertEqual(C.t, 100)

    def test_deliberately_mutable_defaults(self):
        # If a mutable default isn't in the known list of
        #  (list, dict, set), then it's okay.
        class Mutable(object):
            def __init__(self):
                self.l = []

        @dataclass
        class C(object):
            x = field(Mutable)

        # These 2 instances will share this value of x.
        lst = Mutable()
        o1 = C(lst)
        o2 = C(lst)
        self.assertEqual(o1, o2)
        o1.x.l.extend([1, 2])
        self.assertEqual(o1, o2)
        self.assertEqual(o1.x.l, [1, 2])
        self.assertIs(o1.x, o2.x)

    def test_not_other_dataclass(self):
        # Test that some of the problems with namedtuple don't happen
        #  here.
        @dataclass
        class Point3D(object):
            x = field(int)
            y = field(int)
            z = field(int)

        @dataclass
        class Date(object):
            year = field(int)
            month = field(int)
            day = field(int)

        self.assertNotEqual(Point3D(2017, 6, 3), Date(2017, 6, 3))
        self.assertNotEqual(Point3D(1, 2, 3), (1, 2, 3))

        # Make sure we can't unpack.
        with self.assertRaisesRegexp(TypeError, "'Point3D' object is not iterable"):
            x, y, z = Point3D(4, 5, 6)

        # Make sure another class with the same field names isn't
        #  equal.
        @dataclass
        class Point3Dv1(object):
            x = field(int, 0)
            y = field(int, 0)
            z = field(int, 0)
        self.assertNotEqual(Point3D(0, 0, 0), Point3Dv1())
    @unittest.skip(" we can't check this in pyton 2")
    def test_function_annotations(self):
        # Some dummy class and instance to use as a default.
        class F(object):
            pass
        f = F()

        def validate_class(cls):
            # First, check __annotations__, even though they're not
            #  function annotations.
            self.assertEqual(cls.__annotations__['i'], int)
            self.assertEqual(cls.__annotations__['j'], str)
            self.assertEqual(cls.__annotations__['k'], F)
            self.assertEqual(cls.__annotations__['l'], float)
            self.assertEqual(cls.__annotations__['z'], complex)

            # Verify __init__.

            signature = funcsigs.signature(cls.__init__)
            # Check the return type, should be None.
            self.assertIs(signature.return_annotation, None)

            # Check each parameter.
            params = iter(signature.parameters.values())
            param = next(params)
            # This is testing an internal name, and probably shouldn't be tested.
            self.assertEqual(param.name, 'self')
            param = next(params)
            self.assertEqual(param.name, 'i')
            self.assertIs   (param.annotation, int)
            self.assertEqual(param.default, funcsigs.Parameter.empty)
            self.assertEqual(param.kind, funcsigs.Parameter.POSITIONAL_OR_KEYWORD)
            param = next(params)
            self.assertEqual(param.name, 'j')
            self.assertIs   (param.annotation, str)
            self.assertEqual(param.default, funcsigs.Parameter.empty)
            self.assertEqual(param.kind, funcsigs.Parameter.POSITIONAL_OR_KEYWORD)
            param = next(params)
            self.assertEqual(param.name, 'k')
            self.assertIs   (param.annotation, F)
            # Don't test for the default, since it's set to MISSING.
            self.assertEqual(param.kind, funcsigs.Parameter.POSITIONAL_OR_KEYWORD)
            param = next(params)
            self.assertEqual(param.name, 'l')
            self.assertIs   (param.annotation, float)
            # Don't test for the default, since it's set to MISSING.
            self.assertEqual(param.kind, funcsigs.Parameter.POSITIONAL_OR_KEYWORD)
            self.assertRaises(StopIteration, next, params)


        @dataclass
        class C(object):
            i = field(int)
            j = field(str)
            k = field(F, f)
            l = field(float, default=None)
            z = field(complex, default=3+4j, init=False)

        validate_class(C)

        # Now repeat with __hash__.
        @dataclass(frozen=True, unsafe_hash=True)
        class C(object):
            i = field(int)
            j = field(str)
            k = field(F, f)
            l = field(float, default=None)
            z = field(complex, default=3+4j, init=False)

        validate_class(C)

    def test_missing_repr(self):
        self.assertIn('MISSING_TYPE object', repr(MISSING))

    def test_dont_include_other_annotations(self):
        @dataclass
        class C(object):
            i = field(int)
            def foo(self):
                return 4
            @property
            def bar(self):
                return 5
        self.assertEqual(list(C.__annotations__), ['i'])
        self.assertEqual(C(10).foo(), 4)
        self.assertEqual(C(10).bar, 5)
        self.assertEqual(C(10).i, 10)

    def test_post_init_super(self):
        # Make sure super() post-init isn't called by default.
        class B(object):
            def __post_init__(self):
                raise CustomError()

        @dataclass
        class C(B):
            def __post_init__(self):
                self.x = 5

        self.assertEqual(C().x, 5)

        # Now call super(), and it will raise.
        @dataclass
        class C(B):
            def __post_init__(self):
                super(C, self).__post_init__()

        with self.assertRaises(CustomError):
            C()

        # Make sure post-init is called, even if not defined in our
        #  class.
        @dataclass
        class C(B):
            pass

        with self.assertRaises(CustomError):
            C()

    def test_post_init_staticmethod(self):
        flag = [False]
        @dataclass
        class C(object):
            x = field(int)
            y = field(int)
            @staticmethod
            def __post_init__():
                flag[0] = True

        self.assertFalse(flag[0])
        c = C(3, 4)
        self.assertEqual((c.x, c.y), (3, 4))
        self.assertTrue(flag[0])

    def test_post_init_classmethod(self):
        @dataclass
        class C(object):
            flag = False
            x = field(int)
            y = field(int)
            @classmethod
            def __post_init__(cls):
                cls.flag = True

        self.assertFalse(C.flag)
        c = C(3, 4)
        self.assertEqual((c.x, c.y), (3, 4))
        self.assertTrue(C.flag)

    def test_post_init_not_auto_added(self):
        # See bpo-46757, which had proposed always adding __post_init__.  As
        # Raymond Hettinger pointed out, that would be a breaking change.  So,
        # add a test to make sure that the current behavior doesn't change.

        @dataclass
        class A0(object):
            pass

        @dataclass
        class B0(object):
            b_called = field(bool, False)
            def __post_init__(self):
                self.b_called = True

        @dataclass
        class C0(A0, B0):
            c_called = field(bool, False)
            def __post_init__(self):
                super(C0, self).__post_init__()
                self.c_called = True

        # Since A0 has no __post_init__, and one wasn't automatically added
        # (because that's the rule: it's never added by @dataclass, it's only
        # the class author that can add it), then B0.__post_init__ is called.
        # Verify that.
        c = C0()
        self.assertTrue(c.b_called)
        self.assertTrue(c.c_called)

        ######################################
        # Now, the same thing, except A1 defines __post_init__.
        @dataclass
        class A1(object):
            def __post_init__(self):
                pass

        @dataclass
        class B1(object):
            b_called = field(bool, False)
            def __post_init__(self):
                self.b_called = True

        @dataclass
        class C1(A1, B1):
            c_called = field(bool, False)
            def __post_init__(self):
                super(C1, self).__post_init__()
                self.c_called = True

        # This time, B1.__post_init__ isn't being called.  This mimics what
        # would happen if A1.__post_init__ had been automatically added,
        # instead of manually added as we see here.  This test isn't really
        # needed, but I'm including it just to demonstrate the changed
        # behavior when A1 does define __post_init__.
        c = C1()
        self.assertFalse(c.b_called)
        self.assertTrue(c.c_called)

    def test_field_metadata_default(self):
        @dataclass
        class C(object):
            i = field(int)

        self.assertFalse(fields(C)[0].metadata)
        self.assertEqual(len(fields(C)[0].metadata), 0)
        with self.assertRaisesRegexp(TypeError,
                                     'does not support item assignment'):
            fields(C)[0].metadata['test'] = 3

    def test_field_metadata_mapping(self):
        with self.assertRaises(TypeError):
            @dataclass
            class C(object):
                i = field(int, metadata=0)

        d = {}
        @dataclass
        class C(object):
            i = field(int, metadata=d)
        self.assertFalse(fields(C)[0].metadata)
        self.assertEqual(len(fields(C)[0].metadata), 0)
        d['foo'] = 1
        self.assertEqual(len(fields(C)[0].metadata), 1)
        self.assertEqual(fields(C)[0].metadata['foo'], 1)
        with self.assertRaisesRegexp(TypeError,
                                     'does not support item assignment'):
            fields(C)[0].metadata['test'] = 3

        d = {'test': 10, 'bar': '42', 3: 'three'}
        @dataclass
        class C(object):
            i = field(int, metadata=d)
        self.assertEqual(len(fields(C)[0].metadata), 3)
        self.assertEqual(fields(C)[0].metadata['test'], 10)
        self.assertEqual(fields(C)[0].metadata['bar'], '42')
        self.assertEqual(fields(C)[0].metadata[3], 'three')
        d['foo'] = 1
        self.assertEqual(len(fields(C)[0].metadata), 4)
        self.assertEqual(fields(C)[0].metadata['foo'], 1)
        with self.assertRaises(KeyError):
            fields(C)[0].metadata['baz']
        with self.assertRaisesRegexp(TypeError,
                                     'does not support item assignment'):
            fields(C)[0].metadata['test'] = 3

    def test_field_metadata_custom_mapping(self):
        # Try a custom mapping.
        class SimpleNameSpace(object):
            def __init__(self, **kw):
                self.__dict__.update(kw)

            def __getitem__(self, item):
                if item == 'xyzzy':
                    return 'plugh'
                return getattr(self, item)

            def __len__(self):
                return self.__dict__.__len__()

        @dataclass
        class C(object):
            i = field(int, metadata=SimpleNameSpace(a=10))

        self.assertEqual(len(fields(C)[0].metadata), 1)
        self.assertEqual(fields(C)[0].metadata['a'], 10)
        with self.assertRaises(AttributeError):
            fields(C)[0].metadata['b']
        # Make sure we're still talking to our custom mapping.
        self.assertEqual(fields(C)[0].metadata['xyzzy'], 'plugh')

    def test_generic_dataclasses(self):
        from typing import TypeVar
        T = TypeVar('T')

        @dataclass
        class LabeledBox(object):
            content = field(T)
            label = field(str, 'unknown')

        box = LabeledBox(42)
        self.assertEqual(box.content, 42)
        self.assertEqual(box.label, 'unknown')

    def test_generic_extending(self):
        from typing import TypeVar
        S = TypeVar('S')
        T = TypeVar('T')

        @dataclass
        class Base(object):
            x = field(T)
            y = field(S)

        @dataclass
        class DataDerived(Base):
            new_field = field(str)

        c = DataDerived(0, 'test1', 'test2')
        self.assertEqual(astuple(c), (0, 'test1', 'test2'))

    def test_generic_dynamic(self):
        from typing import TypeVar, Optional
        T = TypeVar('T')

        @dataclass
        class Parent(object):
            x = field(T)

        Child = make_dataclass('Child', [('y', T), ('z', Optional[T], None)],
                               bases=(Parent,), namespace={'other': 42})
        c = Child(1, 2)
        self.assertIsNone(c.z)
        c2 = Child(1, 2, 3)
        self.assertEqual(c2.z, 3)
        self.assertEqual(c2.other, 42)

    def test_dataclasses_pickleable(self):
        @dataclass
        class P(object):
            x = field(int)
            y = field(int, 0)

        @dataclass
        class Q(object):
            x = field(int)
            y = field(int, default=0, init=False)

        @dataclass
        class R(object):
            x = field(int)
            y = field(list, default_factory=list)

        q = Q(1)
        q.y = 2
        samples = [P(1), P(1, 2), Q(1), q, R(1), R(1, [2, 3, 4])]
        with expose_to_test(P, Q, R):
            for sample in samples:
                for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                    with self.subTest(sample=sample, proto=proto):
                        new_sample = pickle.loads(pickle.dumps(sample, proto))
                        self.assertEqual(sample.x, new_sample.x)
                        self.assertEqual(sample.y, new_sample.y)
                        self.assertIsNot(sample, new_sample)
                        new_sample.x = 42
                        another_new_sample = pickle.loads(pickle.dumps(new_sample, proto))
                        self.assertEqual(new_sample.x, another_new_sample.x)
                        self.assertEqual(sample.y, another_new_sample.y)

    def test_dataclasses_qualnames(self):
        @dataclass(order=True, unsafe_hash=True, frozen=True)
        class A(object):
            x = field(int)
            y = field(int)

        self.assertEqual(A.__qualname__, self.__module__+".A")

    def test_class_var(self):
        # Make sure ClassVars are ignored in __init__, __repr__, etc.
        from typing import ClassVar
        @dataclass
        class C(object):
            x = field(int)
            y = field(int, 10)
            z = field(ClassVar[int], 1000)
            w = field(ClassVar[int], 2000)
            t = field(ClassVar[int], 3000)
            s = field(ClassVar, 4000)

        c = C(5)
        self.assertIn('C(x=5, y=10)', repr(c))
        self.assertEqual(len(fields(C)), 2)
        self.assertEqual(c.z, 1000)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)
        self.assertEqual(c.s, 4000)
        C.z += 1
        self.assertEqual(c.z, 1001)
        c = C(20)
        self.assertEqual((c.x, c.y), (20, 10))
        self.assertEqual(c.z, 1001)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)
        self.assertEqual(c.s, 4000)

    def test_class_var_no_default(self):
        # If a ClassVar has no default value, it should not be set on the class.
        from typing import ClassVar
        @dataclass
        class C(object):
            x = field(ClassVar[int])

        self.assertNotIn('x', C.__dict__)

    def test_class_var_default_factory(self):
        # It makes no sense for a ClassVar to have a default factory.
        from typing import ClassVar
        with self.assertRaisesRegexp(TypeError,
                                     'cannot have a default factory'):
            @dataclass
            class C(object):
                x = field(ClassVar[int], default_factory=int)

    def test_class_var_with_default(self):
        # If a ClassVar has a default value, it should be set on the class.
        from typing import ClassVar
        @dataclass
        class C(object):
            x = field(ClassVar[int], 10)
        self.assertEqual(C.x, 10)

    def test_class_var_frozen(self):
        # Make sure ClassVars work even if we're frozen.
        from typing import ClassVar
        @dataclass(frozen=True)
        class C(object):
            x = field(int)
            y = field(int, 10)
            z = field(ClassVar[int], 1000)
            w = field(ClassVar[int], 2000)
            t = field(ClassVar[int], 3000)

        c = C(5)
        self.assertIn('C(x=5, y=10)', repr(c))
        self.assertEqual(len(fields(C)), 2)
        self.assertEqual(c.z, 1000)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)
        C.z += 1
        self.assertEqual(c.z, 1001)
        c = C(20)
        self.assertEqual((c.x, c.y), (20, 10))
        self.assertEqual(c.z, 1001)
        self.assertEqual(c.w, 2000)
        self.assertEqual(c.t, 3000)

    def test_init_var_no_default(self):
        # If an InitVar has no default value, it should not be set on the class.

        @dataclass
        class C(object):
            x = field(InitVar(int))

        self.assertNotIn('x', C.__dict__)

    def test_init_var_default_factory(self):
        # It makes no sense for an InitVar to have a default factory.

        with self.assertRaisesRegexp(TypeError,
                                     'cannot have a default factory'):
            @dataclass
            class C(object):
                x = field(InitVar(int), default_factory=int)

    def test_init_var_with_default(self):
        # If an InitVar has a default value, it should be set on the class.

        @dataclass
        class C(object):
            x = field(InitVar(int), 10)
        self.assertEqual(C.x, 10)

    def test_init_var(self):

        @dataclass
        class C(object):
            x = field(int, None)
            init_param = field(InitVar(int), None)

            def __post_init__(self, init_param):
                if self.x is None:
                    self.x = init_param * 2

        c = C(init_param=10)
        self.assertEqual(c.x, 20)

    def test_init_var_preserve_type(self):

        iv = InitVar(int)
        self.assertEqual(iv.type, int)

    def test_init_var_inheritance(self):

        @dataclass
        class Base(object):
            x = field(int)
            init_base = field(InitVar(int))

        b = Base(0, 10)
        self.assertEqual(vars(b), {'x': 0})

        @dataclass
        class C(Base):
            y = field(int)
            init_derived = field(InitVar(int))

            def __post_init__(self, init_base, init_derived):
                self.x = self.x + init_base
                self.y = self.y + init_derived

        c = C(10, 11, 50, 51)
        self.assertEqual(vars(c), {'x': 21, 'y': 101})

    def test_init_var_name_shadowing(self):
        # Shadowing an InitVar with a property

        @dataclass
        class C(object):
            shadowed = field(InitVar(int))
            _shadowed = field(int, init=False)

            def __post_init__(self, shadowed):
                self._shadowed = shadowed * 2

            @property
            def shadowed(self):
                return self._shadowed * 3

        c = C(5)
        self.assertEqual(c.shadowed, 30)

    def test_default_factory_with_no_init(self):
        # We need a factory with a side effect.
        factory_count = [0]
        def factory():
            factory_count[0] += 1
            return factory_count[0]

        @dataclass
        class C(object):
            x = field(int, default_factory=factory, init=False)

        C().x
        self.assertEqual(factory_count[0], 1)
        C().x
        self.assertEqual(factory_count[0], 2)

    def test_default_factory_not_called_if_value_given(self):
        # We need a factory that we can test if it's been called.
        factory_count = [0]
        def factory():
            factory_count[0] += 1
            return factory_count[0]

        @dataclass
        class C(object):
            x = field(int, default_factory=factory)

        C().x
        self.assertEqual(factory_count[0], 1)
        self.assertEqual(C(10).x, 10)
        self.assertEqual(factory_count[0], 1)
        C().x
        self.assertEqual(factory_count[0], 2)

    def test_default_factory_derived(self):
        @dataclass
        class Foo(object):
            x = field(dict, default_factory=dict)

        @dataclass
        class Bar(Foo):
            y = field(int, 1)

        self.assertEqual(Foo().x, {})
        self.assertEqual(Bar().x, {})
        self.assertEqual(Bar().y, 1)

        @dataclass
        class Baz(Foo):
            pass
        self.assertEqual(Baz().x, {})

    def test_intermediate_non_dataclass(self):
        # Test that an intermediate class that defines annotations
        # does not define fields.
        @dataclass
        class A(object):
            x = field(int)

        class B(A):
            y = 0

        @dataclass
        class C(B):
            z = field(int)

        c = C(1, 3)
        self.assertEqual((c.x, c.z), (1, 3))

    def test_is_dataclass_inheritance(self):
        @dataclass
        class X(object):
            y = field(int)

        class Z(X):
            pass

        self.assertTrue(is_dataclass(X))
        self.assertTrue(is_dataclass(Z))
        z_instance = Z(y=5)
        self.assertTrue(is_dataclass(z_instance))

    def test_is_dataclass_when_getattr_always_returns(self):
        # See bpo-37868.
        class A(object):
            def __getattr__(self, key):
                return 0
        self.assertFalse(is_dataclass(A))
        a = A()
        self.assertFalse(is_dataclass(a))

    def test_helper_asdict_copy_values(self):
        @dataclass
        class C(object):
            x = field(int)
            y = field(list, default_factory=list)
        initial = []
        c = C(1, initial)
        d = asdict(c)
        self.assertEqual(d['y'], initial)
        self.assertIsNot(d['y'], initial)
        c = C(1)
        d = asdict(c)
        d['y'].append(1)
        self.assertEqual(c.y, [])

    def test_helper_asdict_nested(self):
        @dataclass
        class UserId(object):
            token = field(int)
            group = field(int)
        @dataclass
        class User(object):
            name = field(str)
            id = field(UserId)
        u = User('Joe', UserId(123, 1))
        d = asdict(u)
        self.assertEqual(d, {'name': 'Joe', 'id': {'token': 123, 'group': 1}})
        self.assertIsNot(asdict(u), asdict(u))
        u.id.group = 2
        self.assertEqual(asdict(u), {'name': 'Joe', 'id': {'token': 123, 'group': 2}})

    def test_helper_asdict_factory(self):
        @dataclass
        class C(object):
            x = field(int)
            y = field(int)
        c = C(1, 2)
        d = asdict(c, dict_factory=OrderedDict)
        self.assertEqual(d, OrderedDict([('x', 1), ('y', 2)]))
        self.assertIsNot(d, asdict(c, dict_factory=OrderedDict))
        c.x = 42
        d = asdict(c, dict_factory=OrderedDict)
        self.assertEqual(d, OrderedDict([('x', 42), ('y', 2)]))
        self.assertIsInstance(d, OrderedDict)

    def test_helper_asdict_namedtuple(self):
        from collections import namedtuple
        T = namedtuple('T', 'a b c')
        @dataclass
        class C(object):
            x = field(str)
            y = field(T)
        c = C('outer', T(1, C('inner', T(11, 12, 13)), 2))

        d = asdict(c)
        self.assertEqual(d, {'x': 'outer',
                             'y': T(1,
                                    {'x': 'inner',
                                     'y': T(11, 12, 13)},
                                    2),
                             }
                         )

    def test_helper_asdict_namedtuple_key(self):
        from collections import namedtuple
        @dataclass
        class C(object):
            f = field(dict)
        T = namedtuple('T', 'a')

        c = C({T('an a'): 0})

        self.assertEqual(asdict(c), {'f': {T(a='an a'): 0}})

    def test_helper_asdict_namedtuple_derived(self):
        from collections import namedtuple
        class T(namedtuple('Tbase', 'a')):
            def my_a(self):
                return self.a

        @dataclass
        class C(object):
            f = field(T)

        t = T(6)
        c = C(t)

        d = asdict(c)
        self.assertEqual(d, {'f': T(a=6)})
        self.assertIsNot(d['f'], t)
        self.assertEqual(d['f'].my_a(), 6)

    def test_helper_astuple_copy_values(self):
        @dataclass
        class C(object):
            x = field(int)
            y = field(list, default_factory=list)
        initial = []
        c = C(1, initial)
        t = astuple(c)
        self.assertEqual(t[1], initial)
        self.assertIsNot(t[1], initial)
        c = C(1)
        t = astuple(c)
        t[1].append(1)
        self.assertEqual(c.y, [])

    def test_helper_astuple_nested(self):
        @dataclass
        class UserId(object):
            token = field(int)
            group = field(int)
        @dataclass
        class User(object):
            name = field(str)
            id = field(UserId)
        u = User('Joe', UserId(123, 1))
        t = astuple(u)
        self.assertEqual(t, ('Joe', (123, 1)))
        self.assertIsNot(astuple(u), astuple(u))
        u.id.group = 2
        self.assertEqual(astuple(u), ('Joe', (123, 2)))

    def test_helper_astuple_namedtuple(self):
        from collections import namedtuple
        T = namedtuple('T', 'a b c')
        @dataclass
        class C(object):
            x = field(str)
            y = field(T)
        c = C('outer', T(1, C('inner', T(11, 12, 13)), 2))

        t = astuple(c)
        self.assertEqual(t, ('outer', T(1, ('inner', (11, 12, 13)), 2)))

    def test_helper_astuple_factory(self):
        from collections import namedtuple
        @dataclass
        class C(object):
            x = field(int)
            y = field(int)
        NT = namedtuple('NT', 'x y')
        def nt(lst):
            return NT(*lst)
        c = C(1, 2)
        t = astuple(c, tuple_factory=nt)
        self.assertEqual(t, NT(1, 2))
        self.assertIsNot(t, astuple(c, tuple_factory=nt))
        c.x = 42
        t = astuple(c, tuple_factory=nt)
        self.assertEqual(t, NT(42, 2))
        self.assertIsInstance(t, NT)

    def test_helper_asdict_builtin_containers(self):
        from typing import List, Tuple, Dict
        @dataclass
        class User(object):
            name = field(str)
            id = field(int)
        @dataclass
        class GroupList(object):
            id = field(int)
            users = field(List[User])
        @dataclass
        class GroupTuple(object):
            id = field(int)
            users = field(Tuple[User, ...])
        @dataclass
        class GroupDict(object):
            id = field(int)
            users = field(Dict[str, User])
        a = User('Alice', 1)
        b = User('Bob', 2)
        gl = GroupList(0, [a, b])
        gt = GroupTuple(0, (a, b))
        gd = GroupDict(0, {'first': a, 'second': b})
        self.assertEqual(asdict(gl), {'id': 0, 'users': [{'name': 'Alice', 'id': 1},
                                                         {'name': 'Bob', 'id': 2}]})
        self.assertEqual(asdict(gt), {'id': 0, 'users': ({'name': 'Alice', 'id': 1},
                                                         {'name': 'Bob', 'id': 2})})
        self.assertEqual(asdict(gd), {'id': 0, 'users': {'first': {'name': 'Alice', 'id': 1},
                                                         'second': {'name': 'Bob', 'id': 2}}})

    def test_helper_asdict_builtin_object_containers(self):
        @dataclass
        class Child(object):
            d = field(object)

        @dataclass
        class Parent(object):
            child = field(Child)

        self.assertEqual(asdict(Parent(Child([1]))), {'child': {'d': [1]}})
        self.assertEqual(asdict(Parent(Child({1: 2}))), {'child': {'d': {1: 2}}})

    def test_helper_astuple_builtin_containers(self):
        from typing import List, Tuple, Dict
        @dataclass
        class User(object):
            name = field(str)
            id = field(int)
        @dataclass
        class GroupList(object):
            id = field(int)
            users = field(List[User])
        @dataclass
        class GroupTuple(object):
            id = field(int)
            users = field(Tuple[User, ...])
        @dataclass
        class GroupDict(object):
            id = field(int)
            users = field(Dict[str, User])
        a = User('Alice', 1)
        b = User('Bob', 2)
        gl = GroupList(0, [a, b])
        gt = GroupTuple(0, (a, b))
        gd = GroupDict(0, {'first': a, 'second': b})
        self.assertEqual(astuple(gl), (0, [('Alice', 1), ('Bob', 2)]))
        self.assertEqual(astuple(gt), (0, (('Alice', 1), ('Bob', 2))))
        self.assertEqual(astuple(gd), (0, {'first': ('Alice', 1), 'second': ('Bob', 2)}))

    def test_helper_astuple_builtin_object_containers(self):
        @dataclass
        class Child(object):
            d = field(object)

        @dataclass
        class Parent(object):
            child = field(Child)

        self.assertEqual(astuple(Parent(Child([1]))), (([1],),))
        self.assertEqual(astuple(Parent(Child({1: 2}))), (({1: 2},),))

    def test_helper_asdict_defaultdict(self):
        from collections import defaultdict
        try:
            from typing import DefaultDict
        except ImportError:
            DefaultDict = dict

        @dataclass
        class C(object):
            mp = field(DefaultDict)

        dd = defaultdict(list)
        dd["x"].append(12)
        c = C(mp=dd)
        d = asdict(c)

        self.assertEqual(d, {"mp": {"x": [12]}})
        self.assertTrue(d["mp"] is not c.mp)

    def test_helper_astuple_defaultdict(self):
        from collections import defaultdict
        try:
            from typing import DefaultDict
        except ImportError:
            DefaultDict = dict

        @dataclass
        class C(object):
            mp = field(DefaultDict)

        dd = defaultdict(list)
        dd["x"].append(12)
        c = C(mp=dd)
        t = astuple(c)

        self.assertEqual(t, ({"x": [12]},))
        self.assertTrue(t[0] is not dd)

    def test_no_unhashable_default(self):
        # See bpo-44674.
        class Unhashable(object):
            __hash__ = None

        unhashable_re = 'mutable default .* for field a is not allowed'
        with self.assertRaisesRegexp(ValueError, unhashable_re):
            @dataclass
            class A(object):
                a = field(dict, {})

        with self.assertRaisesRegexp(ValueError, unhashable_re):
            @dataclass
            class A(object):
                a = field(object, Unhashable())

    def test_items_in_dicts(self):
        @dataclass
        class C(object):
            a = field(int)
            b = field(list, default_factory=list, init=False)
            c = field(list, default_factory=list)
            d = field(int, default=4, init=False)
            e = field(int, 0)

        c = C(0)
        # Class dict
        self.assertNotIn('a', C.__dict__)
        self.assertNotIn('b', C.__dict__)
        self.assertNotIn('c', C.__dict__)
        self.assertIn('d', C.__dict__)
        self.assertEqual(C.d, 4)
        self.assertIn('e', C.__dict__)
        self.assertEqual(C.e, 0)
        # Instance dict
        self.assertIn('a', c.__dict__)
        self.assertEqual(c.a, 0)
        self.assertIn('b', c.__dict__)
        self.assertEqual(c.b, [])
        self.assertIn('c', c.__dict__)
        self.assertEqual(c.c, [])
        self.assertNotIn('d', c.__dict__)
        self.assertIn('e', c.__dict__)
        self.assertEqual(c.e, 0)

    def test_init_in_order(self):
        @dataclass
        class C(object):
            a = field(int)
            b = field(int)
            c = field(list, default_factory=list, init=False)
            d = field(list, default_factory=list)
            e = field(int, default=4, init=False)
            f = field(int, 4)

        calls = []
        original_setattr = C.__setattr__
        def setattr(self, name, value):
            calls.append((name, value))
            original_setattr(self, name, value)

        C.__setattr__ = setattr
        c = C(0, 1)
        self.assertEqual(('a', 0), calls[0])
        self.assertEqual(('b', 1), calls[1])

    def test_alternate_classmethod_constructor(self):
        @dataclass
        class C(object):
            x = field(int)
            @classmethod
            def from_file(cls, filename):
                value_in_file = 20
                return cls(value_in_file)

        self.assertEqual(C.from_file('filename').x, 20)

    def test_clean_traceback_from_fields_exception(self):
        import io
        import traceback
        stdout = io.StringIO()
        try:
            fields(object)
        except TypeError as exc:
            s =traceback.format_exc(10)
            print(s.decode("utf-8"), file=stdout)
            #traceback.print_exception(type(exc), exc, sys.exc_info()[2], file=stdout)
        printed_traceback = stdout.getvalue()
        self.assertNotIn("AttributeError", printed_traceback)
        self.assertNotIn("__dataclass_fields__", printed_traceback)

    def test_incomplete_annotations(self):
        @dataclass
        class C(object):
            pass

        # For now, just make sure it doesn't crash
        _ = C()

    def test_classvar_default_factory(self):
        # It's an error for a ClassVar to have a factory function.
        from typing import ClassVar
        with self.assertRaisesRegexp(TypeError,
                                     'cannot have a default factory'):
            @dataclass
            class C(object):
                x = field(ClassVar[int], default_factory=int)

    def test_is_dataclass_genericalias(self):

        @dataclass
        class A(types.GenericAlias):
            origin = field(type)
            args = field(type)
        self.assertTrue(is_dataclass(A))
        a = A(list, int)
        self.assertTrue(is_dataclass(type(a)))
        self.assertTrue(is_dataclass(a))
