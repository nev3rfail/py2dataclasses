# Port of dataclasses tests to Python 2.7
from __future__ import print_function, absolute_import

import contextlib
import os.path

import sys
import abc

import typing
from collections import OrderedDict

path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.append(path)
from dataclasses import fields, field, Field, dataclass, is_dataclass, replace, make_dataclass, of, asdict, \
    astuple, FrozenInstanceError, MISSING, _oneshot
import unittest2 as unittest
import pickle
import copy
import sys
import types
import weakref
# Just any custom exception we can catch.
class CustomError(Exception): pass
class ABC(object):
    __metaclass__ = abc.ABCMeta
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
            self.assertIn(type(f), [Field, _oneshot])
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

    def test_no_init(self):
        @dataclass(init=False)
        class C(object):
            #__annotations__ = {'i': int}
            i = 0

        self.assertEqual(C().i, 0)

        @dataclass(init=False)
        class C(object):
            #__annotations__ = {'i': int}
            i = 2

            def __init__(self):
                self.i = 3

        self.assertEqual(C().i, 3)

    def test_no_repr(self):
        # Test a class with no __repr__ and repr=False.
        @dataclass(repr=False)
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int)

        self.assertIn('C object at', repr(C(3)))

    def test_no_eq(self):
        # Test a class with no __eq__ and eq=False.
        @dataclass(eq=False)
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int)

        self.assertNotEqual(C(0), C(0))
        c = C(3)
        self.assertEqual(c, c)

    def test_frozen(self):
        @dataclass(frozen=True)
        class C(object):
            #__annotations__ = {'i': int}
            i = field(int)

        c = C(10)
        self.assertEqual(c.i, 10)
        with self.assertRaises(FrozenInstanceError):
            c.i = 5
        self.assertEqual(c.i, 10)

    def test_frozen_hash(self):
        @dataclass(frozen=True)
        class C(object):
            #__annotations__ = {'x': object}
            x = field(object)

        # If x is immutable, we can compute the hash.
        hash(C(3))

        # If x is mutable, computing the hash is an error.
        with self.assertRaisesRegexp(TypeError, 'unhashable type'):
            hash(C({}))

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


class TestMakeDataclass(unittest.TestCase):
    def test_simple(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', int, field(int, default=5))],
                           namespace={'add_one': lambda self: self.x + 1})
        c = C(10)
        self.assertEqual((c.x, c.y), (10, 5))
        self.assertEqual(c.add_one(), 11)

    def test_no_mutate_namespace(self):
        # Make sure a provided namespace isn't mutated.
        ns = {}
        C = make_dataclass('C',
                           [('x', int),
                            ('y', int, field(int, default=5))],
                           namespace=ns)
        self.assertEqual(ns, {})

    def test_base(self):
        class Base1(object):
            pass
        class Base2(object):
            pass
        C = make_dataclass('C',
                           [('x', int)],
                           bases=(Base1, Base2))
        c = C(2)
        self.assertIsInstance(c, C)
        self.assertIsInstance(c, Base1)
        self.assertIsInstance(c, Base2)

    def test_base_dataclass(self):
        @dataclass
        class Base1(object):
            #__annotations__ = {'x': int}
            x = field(int)

        class Base2(object):
            pass

        C = make_dataclass('C',
                           [('y', int)],
                           bases=(Base1, Base2))
        with self.assertRaisesRegexp(TypeError, '__init__\(\) takes exactly 3 arguments \(2 given\)'):
            c = C(2)
        c = C(1, 2)
        self.assertIsInstance(c, C)
        self.assertIsInstance(c, Base1)
        self.assertIsInstance(c, Base2)

        self.assertEqual((c.x, c.y), (1, 2))

    def test_no_types(self):
        C = make_dataclass('Point', ['x', 'y', 'z'])
        c = C(1, 2, 3)
        self.assertEqual(vars(c), {'x': 1, 'y': 2, 'z': 3})

        C = make_dataclass('Point', ['x', ('y', int), 'z'])
        c = C(1, 2, 3)
        self.assertEqual(vars(c), {'x': 1, 'y': 2, 'z': 3})


class TestReplace(unittest.TestCase):
    def test(self):
        @dataclass(frozen=True)
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int)

        c = C(1, 2)
        c1 = replace(c, x=3)
        self.assertEqual(c1.x, 3)
        self.assertEqual(c1.y, 2)

    def test_frozen(self):
        @dataclass(frozen=True)
        class C(object):
            #__annotations__ = {'x': int, 'y': int, 'z': int, 't': int}
            x = field(_typ=int)
            y = field(_typ=int)
            z = field(_typ=int, init=False, default=10)
            t = field(_typ=int, init=False, default=100)

        c = C(1, 2)
        c1 = replace(c, x=3)
        self.assertEqual((c.x, c.y, c.z, c.t), (1, 2, 10, 100))
        self.assertEqual((c1.x, c1.y, c1.z, c1.t), (3, 2, 10, 100))

        with self.assertRaisesRegexp(TypeError, 'init=False'):
            replace(c, x=3, z=20, t=50)
        with self.assertRaisesRegexp(TypeError, 'init=False'):
            replace(c, z=20)

        # Make sure the result is still frozen.
        with self.assertRaisesRegexp(FrozenInstanceError, "cannot assign to field 'x'"):
            c1.x = 3

    def test_invalid_field_name(self):
        @dataclass(frozen=True)
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int)

        c = C(1, 2)
        with self.assertRaisesRegexp(TypeError, r"__init__\(\) got an unexpected "
                                                "keyword argument 'z'"):
            c1 = replace(c, z=3)

    def test_invalid_object(self):
        @dataclass(frozen=True)
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int)

        with self.assertRaisesRegexp(TypeError, 'dataclass instance'):
            replace(C, x=3)

        with self.assertRaisesRegexp(TypeError, 'dataclass instance'):
            replace(0, x=3)

    def test_no_init(self):
        @dataclass
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int, init=False, default=10)

        c = C(1)
        c.y = 20

        # Make sure y gets the default value.
        c1 = replace(c, x=5)
        self.assertEqual((c1.x, c1.y), (5, 10))

        # Trying to replace y is an error.
        with self.assertRaisesRegexp(TypeError, 'init=False'):
            replace(c, x=2, y=30)

        with self.assertRaisesRegexp(TypeError, 'init=False'):
            replace(c, y=30)

@unittest.skip
class TestDocString(unittest.TestCase):
    def assertDocStrEqual(self, a, b):
        # Because 3.6 and 3.7 differ in how inspect.signature work
        #  (see bpo #32108), for the time being just compare them with
        #  whitespace stripped.
        self.assertEqual(a.replace(' ', ''), b.replace(' ', ''))

    def test_existing_docstring_not_overridden(self):
        @dataclass
        class C(object):
            """Lorem ipsum"""
            x = field(int)

        self.assertEqual(C.__doc__, "Lorem ipsum")

    def test_docstring_no_fields(self):
        @dataclass
        class C(object):
            pass

        self.assertDocStrEqual(C.__doc__, "C()")

    def test_docstring_one_field(self):
        @dataclass
        class C(object):
            x = field(int)

        self.assertDocStrEqual(C.__doc__, "C(x:int)")

    def test_docstring_two_fields(self):
        @dataclass
        class C(object):
            x = field(int)
            y = field(int)

        self.assertDocStrEqual(C.__doc__, "C(x:int, y:int)")

    def test_docstring_three_fields(self):
        @dataclass
        class C(object):
            x = field(int)
            y = field(int)
            z = field(str)

        self.assertDocStrEqual(C.__doc__, "C(x:int, y:int, z:str)")

    def test_docstring_one_field_with_default(self):
        @dataclass
        class C(object):
            x = field(int, default=3)

        self.assertDocStrEqual(C.__doc__, "C(x:int=3)")

    def test_docstring_list_field(self):
        @dataclass
        class C(object):
            x = field(list)

        self.assertDocStrEqual(C.__doc__, "C(x:list)")

    def test_docstring_list_field_with_default_factory(self):
        @dataclass
        class C(object):
            x = field(list, default_factory=list)

        self.assertDocStrEqual(C.__doc__, "C(x:list=<factory>)")

    def test_docstring_undefined_name(self):
        @dataclass
        class C(object):
            x = field('undef')

        self.assertDocStrEqual(C.__doc__, "C(x:undef)")


class TestInit(unittest.TestCase):
    def test_base_has_init(self):
        class B(object):
            def __init__(self):
                self.z = 100

        # Make sure that declaring this class doesn't raise an error.
        #  The issue is that we can't override __init__ in our class,
        #  but it should be okay to add __init__ to us if our base has
        #  an __init__.
        @dataclass
        class C(B):
            x = field(int, default=0)
        c = C(10)
        self.assertEqual(c.x, 10)
        self.assertNotIn('z', vars(c))

        # Make sure that if we don't add an init, the base __init__
        #  gets called.
        @dataclass(init=False)
        class C(B):
            x = field(int, default=10)
        c = C()
        self.assertEqual(c.x, 10)
        self.assertEqual(c.z, 100)

    def test_no_init(self):
        @dataclass(init=False)
        class C(object):
            i = field(int, default=0)
        self.assertEqual(C().i, 0)

        @dataclass(init=False)
        class C(object):
            i = field(int, default=2)
            def __init__(self):
                self.i = 3
        self.assertEqual(C().i, 3)

    def test_overwriting_init(self):
        # If the class has __init__, use it no matter the value of
        #  init=.

        @dataclass
        class C(object):
            x = field(int)
            def __init__(self, x):
                self.x = 2 * x
        self.assertEqual(C(3).x, 6)

        @dataclass(init=True)
        class C(object):
            x = field(int)
            def __init__(self, x):
                self.x = 2 * x
        self.assertEqual(C(4).x, 8)

        @dataclass(init=False)
        class C(object):
            x = field(int)
            def __init__(self, x):
                self.x = 2 * x
        self.assertEqual(C(5).x, 10)


class TestRepr(unittest.TestCase):
    def test_repr(self):
        @dataclass
        class B(object):
            x = field(int)

        @dataclass
        class C(B):
            y = field(int, default=10)

        o = C(4)
        # Basic repr test - just verify it contains the values
        repr_str = repr(o)
        self.assertIn('C', repr_str)
        self.assertIn('4', repr_str)
        self.assertIn('10', repr_str)

        @dataclass
        class D(C):
            x = field(int, default=20)
        repr_str = repr(D())
        self.assertIn('D', repr_str)
        self.assertIn('20', repr_str)
        self.assertIn('10', repr_str)

    def test_no_repr(self):
        # Test a class with no __repr__ and repr=False.
        @dataclass(repr=False)
        class C(object):
            x = field(int)
        repr_str = repr(C(3))
        self.assertIn('C object at', repr_str)

        # Test a class with a __repr__ and repr=False.
        @dataclass(repr=False)
        class C(object):
            x = field(int)
            def __repr__(self):
                return 'C-class'
        self.assertEqual(repr(C(3)), 'C-class')

    def test_overwriting_repr(self):
        # If the class has __repr__, use it no matter the value of
        #  repr=.

        @dataclass
        class C(object):
            x = field(int)
            def __repr__(self):
                return 'x'
        self.assertEqual(repr(C(0)), 'x')

        @dataclass(repr=True)
        class C(object):
            x = field(int)
            def __repr__(self):
                return 'x'
        self.assertEqual(repr(C(0)), 'x')

        @dataclass(repr=False)
        class C(object):
            x = field(int)
            def __repr__(self):
                return 'x'
        self.assertEqual(repr(C(0)), 'x')


class TestEq(unittest.TestCase):
    def test_recursive_eq(self):
        # Test a class with recursive child
        @dataclass
        class C(object):
            recursive = field(object, default=types.EllipsisType)
        c = C()
        c.recursive = c
        self.assertEqual(c, c)

    def test_no_eq(self):
        # Test a class with no __eq__ and eq=False.
        @dataclass(eq=False)
        class C(object):
            x = field(int)
        self.assertNotEqual(C(0), C(0))
        c = C(3)
        self.assertEqual(c, c)

        # Test a class with an __eq__ and eq=False.
        @dataclass(eq=False)
        class C(object):
            x = field(int)
            def __eq__(self, other):
                return other == 10
        self.assertEqual(C(3), 10)

    def test_overwriting_eq(self):
        # If the class has __eq__, use it no matter the value of
        #  eq=.

        @dataclass
        class C(object):
            x = field(int)
            def __eq__(self, other):
                return other == 3
        self.assertEqual(C(1), 3)
        self.assertNotEqual(C(1), 1)

        @dataclass(eq=True)
        class C(object):
            x = field(int)
            def __eq__(self, other):
                return other == 4
        self.assertEqual(C(1), 4)
        self.assertNotEqual(C(1), 1)

        @dataclass(eq=False)
        class C(object):
            x = field(int)
            def __eq__(self, other):
                return other == 5
        self.assertEqual(C(1), 5)
        self.assertNotEqual(C(1), 1)


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

        self.assertTrue(C(0) < -1)
        self.assertTrue(C(0) <= -1)
        self.assertTrue(C(0) > 1)
        self.assertTrue(C(0) >= 1)

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
                                    'Cannot overwrite attribute __lt__'):
            @dataclass(order=True)
            class C(object):
                x = field(int)
                def __lt__(self):
                    pass

        with self.assertRaisesRegexp(TypeError,
                                    'Cannot overwrite attribute __le__'):
            @dataclass(order=True)
            class C(object):
                x = field(int)
                def __le__(self):
                    pass

        with self.assertRaisesRegexp(TypeError,
                                    'Cannot overwrite attribute __gt__'):
            @dataclass(order=True)
            class C(object):
                x = field(int)
                def __gt__(self):
                    pass

        with self.assertRaisesRegexp(TypeError,
                                    'Cannot overwrite attribute __ge__'):
            @dataclass(order=True)
            class C(object):
                x = field(int)
                def __ge__(self):
                    pass


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


class TestFrozen(unittest.TestCase):
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

    def test_frozen_no_init(self):
        @dataclass(frozen=True, init=False)
        class C(object):
            i = field(int, default=0)

        c = C()
        self.assertEqual(c.i, 0)
        with self.assertRaises(FrozenInstanceError):
            c.i = 5

    def test_frozen_fields_with_defaults(self):
        @dataclass(frozen=True)
        class C(object):
            x = field(int)
            y = field(int, default=5)
            z = field(int, default_factory=list)

        c = C(3)
        self.assertEqual((c.x, c.y, c.z), (3, 5, []))
        with self.assertRaises(FrozenInstanceError):
            c.x = 10

    def test_frozen_field_no_default(self):
        @dataclass(frozen=True)
        class C(object):
            x = field(int)

        c = C(10)
        self.assertEqual(c.x, 10)
        with self.assertRaisesRegexp(FrozenInstanceError, "cannot assign to field 'x'"):
            c.x = 5
        self.assertEqual(c.x, 10)


class TestAbstract(unittest.TestCase):
    def test_abc_implementation(self):
        #
        import inspect

        class Ordered(object):
            __metaclass__ = abc.ABCMeta
            @abc.abstractmethod
            def __lt__(self, other):
                pass

            @abc.abstractmethod
            def __le__(self, other):
                pass

        @dataclass(order=True)
        class Date(Ordered):
            """yay doc"""
            year = field(int)
            month = field(str)
            day = field(int)

        self.assertFalse(inspect.isabstract(Date))
        self.assertGreater(Date(2020, 12, 25), Date(2020, 8, 31))

    def test_maintain_abc(self):
        
        import inspect

        class A(ABC):
            @abc.abstractmethod
            def foo(self):
                pass

        @dataclass
        class Date(A):
            year = field(int)
            month = field(str)
            day = field(int)

        self.assertTrue(inspect.isabstract(Date))
        msg = "Can't instantiate abstract class Date with abstract methods foo"
        self.assertRaisesRegexp(TypeError, msg, Date)


class TestMatchArgs(unittest.TestCase):
    def test_match_args(self):
        @dataclass
        class C(object):
            a = field(int)
        self.assertEqual(C(42).__match_args__, ('a',))

    def test_explicit_match_args(self):
        ma = ()
        @dataclass
        class C(object):
            a = field(int)
            __match_args__ = ma
        self.assertIs(C(42).__match_args__, ma)

    def test_bpo_43764(self):
        @dataclass(repr=False, eq=False, init=False)
        class X(object):
            a = field(int)
            b = field(int)
            c = field(int)
        self.assertEqual(X.__match_args__, ("a", "b", "c"))

    def test_match_args_argument(self):
        @dataclass(match_args=False)
        class X(object):
            a = field(int)
        self.assertNotIn('__match_args__', X.__dict__)

        @dataclass(match_args=False)
        class Y(object):
            a = field(int)
            __match_args__ = ('b',)
        self.assertEqual(Y.__match_args__, ('b',))

        @dataclass(match_args=False)
        class Z(Y):
            z = field(int)
        self.assertEqual(Z.__match_args__, ('b',))

        # Ensure parent dataclass __match_args__ is seen, if child class
        # specifies match_args=False.
        @dataclass
        class A(object):
            a = field(int)
            z = field(int)
        @dataclass(match_args=False)
        class B(A):
            b = field(int)
        self.assertEqual(B.__match_args__, ('a', 'z'))

    def test_make_dataclasses(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', int)])
        self.assertEqual(C.__match_args__, ('x', 'y'))

        C = make_dataclass('C',
                           [('x', int),
                            ('y', int)],
                           match_args=True)
        self.assertEqual(C.__match_args__, ('x', 'y'))

        C = make_dataclass('C',
                           [('x', int),
                            ('y', int)],
                           match_args=False)
        self.assertNotIn('__match_args__', C.__dict__)

        C = make_dataclass('C',
                           [('x', int),
                            ('y', int)],
                           namespace={'__match_args__': ('z',)})
        self.assertEqual(C.__match_args__, ('z',))


class TestKeywordArgs(unittest.TestCase):
    def test_field_marked_as_kwonly(self):
        # Test kw_only flag on fields
        @dataclass(kw_only=True)
        class A(object):
            a = field(int)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass(kw_only=True)
        class A(object):
            a = field(int, kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass(kw_only=True)
        class A(object):
            a = field(int, kw_only=False)
        self.assertFalse(fields(A)[0].kw_only)

        # Using dataclass(kw_only=False)
        @dataclass(kw_only=False)
        class A(object):
            a = field(int)
        self.assertFalse(fields(A)[0].kw_only)

        @dataclass(kw_only=False)
        class A(object):
            a = field(int, kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass(kw_only=False)
        class A(object):
            a = field(int, kw_only=False)
        self.assertFalse(fields(A)[0].kw_only)

        # Not specifying dataclass(kw_only)
        @dataclass
        class A(object):
            a = field(int)
        self.assertFalse(fields(A)[0].kw_only)

        @dataclass
        class A(object):
            a = field(int, kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        @dataclass
        class A(object):
            a = field(int, kw_only=False)
        self.assertFalse(fields(A)[0].kw_only)

    def test_match_args(self):
        # kw fields don't show up in __match_args__.
        @dataclass(kw_only=True)
        class C(object):
            a = field(int)
        self.assertEqual(C(a=42).__match_args__, ())

        @dataclass
        class C(object):
            a = field(int)
            b = field(int, kw_only=True)
        self.assertEqual(C(42, b=10).__match_args__, ('a',))


class TestFieldNoAnnotation(unittest.TestCase):
    def test_field_without_annotation(self):
        with self.assertRaisesRegexp(TypeError,
                                     "'f' is a field but has no type annotation"):
            @dataclass
            class TEST_NO_ANNOTATION(object):
                f = field()

            pass


class TestDescriptors(unittest.TestCase):
    def test_set_name(self):
        # See bpo-33141.

        # Create a descriptor.
        class D(object):
            def __set_name__(self, owner, name):
                self.name = name + 'x'
            def __get__(self, instance, owner):
                if instance is not None:
                    return 1
                return self

        # This is the case of just normal descriptor behavior, no
        #  dataclass code is involved in initializing the descriptor.
        @dataclass
        class C(object):
            c = field(int, default=D())
        self.assertEqual(C.c.name, 'cx')

        # Now test with a default value and init=False, which is the
        #  only time this is really meaningful.  If not using
        #  init=False, then the descriptor will be overwritten, anyway.
        @dataclass
        class C(object):
            c = field(int, default=D(), init=False)
        self.assertEqual(C.c.name, 'cx')
        self.assertEqual(C().c, 1)

    def test_non_descriptor(self):
        # PEP 487 says __set_name__ should work on non-descriptors.
        # Create a descriptor.

        class D(object):
            def __set_name__(self, owner, name):
                self.name = name + 'x'

        @dataclass
        class C(object):
            c = field(int, default=D(), init=False)
        self.assertEqual(C.c.name, 'cx')

    def test_lookup_on_instance(self):
        # See bpo-33175.
        class D(object):
            pass

        d = D()
        # Create an attribute on the instance, not type.
        d.__set_name__ = lambda owner, name: None

        # Make sure d.__set_name__ is not called.
        @dataclass
        class C(object):
            i = field(int, default=d, init=False)

        # If we got here without error, test passes

    def test_lookup_on_class(self):
        # See bpo-33175.
        class D(object):
            called = False
            def __set_name__(self, owner, name):
                D.called = True

        # Make sure D.__set_name__ is called.
        @dataclass
        class C(object):
            i = field(int, default=D(), init=False)

        self.assertTrue(D.called)

    def test_init_calls_set(self):
        class D(object):
            set_called = False
            def __set__(self, instance, value):
                D.set_called = True

        @dataclass
        class C(object):
            i = field(D, default=D())

        # Make sure D.__set__ is called.
        D.set_called = False
        c = C(D())
        self.assertTrue(D.set_called)

    def test_getting_field_calls_get(self):
        class D(object):
            get_called = False
            def __get__(self, instance, owner):
                D.get_called = True
                return 42
            def __set__(self, instance, value):
                pass

        @dataclass
        class C(object):
            i = field(D, default=D())

        c = C(D())

        # Make sure D.__get__ is called.
        D.get_called = False
        value = c.i
        self.assertTrue(D.get_called)

    def test_setting_field_calls_set(self):
        class D(object):
            set_called = False
            def __set__(self, instance, value):
                D.set_called = True

        @dataclass
        class C(object):
            i = field(D, default=D())

        c = C(D())

        # Make sure D.__set__ is called.
        D.set_called = False
        c.i = D()
        self.assertTrue(D.set_called)

    def test_setting_uninitialized_descriptor_field(self):
        class D(object):
            set_called = False
            def __set__(self, instance, value):
                D.set_called = True

        @dataclass
        class C(object):
            i = field(D)

        # D.__set__ is not called because there's no D instance to call it on
        D.set_called = False
        c = C(D())
        self.assertFalse(D.set_called)

        # D.__set__ still isn't called after setting i to an instance of D
        # because descriptors don't behave like that when stored as instance vars
        c.i = D()
        c.i = 5
        self.assertFalse(D.set_called)

    def test_default_value(self):
        class D(object):
            def __get__(self, instance, owner):
                if instance is None:
                    return 100

                return instance._x

            def __set__(self, instance, value):
                #f = sys._getframe(0)
                #f1 = sys._getframe(1)
                instance._x = value

        @dataclass
        class C(object):
            i = field(D, D(), mode=1)

        c = C()
        self.assertEqual(c.i, 100)

        c = C(5)
        # The descriptor's __get__ will be called
        self.assertEqual(c.i, 5)

    def test_no_default_value(self):
        class D(object):
            def __get__(self, instance, owner):
                if instance is None:
                    raise AttributeError()
                return instance._x

            def __set__(self, instance, value):
                instance._x = value

        @dataclass
        class C(object):
            i = field(D, default=D())

        with self.assertRaisesRegexp(TypeError, '__init__\(\) takes exactly 2 arguments \(1 given\)'):
            c = C()


if __name__ == '__main__':
    unittest.main()

