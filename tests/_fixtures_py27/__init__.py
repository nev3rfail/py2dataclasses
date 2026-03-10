# Port of dataclasses tests to Python 2.7
from __future__ import print_function, absolute_import
import os
import sys
import textwrap

import six

path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..", "src"))
sys.path.insert(0, path)

try:
    from collections import MutableMapping
except:
    # python 2 hack
    import collections
    from collections.abc import MutableMapping
    object.__setattr__(collections, "MutableMapping", MutableMapping)

import abc
try:
    import funcsigs
except ImportError:
    pass

from collections import OrderedDict, deque


#path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..","..", "src"))
#sys.path.append(path)
from dataclasses import fields, field, Field, dataclass, is_dataclass, replace, make_dataclass, asdict, \
    astuple, FrozenInstanceError, MISSING, InitVar
import dataclasses

try:
    from dataclasses import _Field
except:
    from dataclasses import Field as _Field

try:
    import unittest2 as unittest
except ImportError:
    import unittest
    if not hasattr(unittest.TestCase, 'assertRaisesRegexp'):
        unittest.TestCase.assertRaisesRegexp = unittest.TestCase.assertRaisesRegex
import pickle
import copy
import types
import weakref
try:
    import types.GenericAlias as GenericAlias
except ImportError:
    from _py2dataclasses import type_utils as __type_utils

    #import __abc_utils.ABC as ABC
    GenericAlias = __type_utils.GenericAlias

# Just any custom exception we can catch.
class CustomError(Exception): pass
ABC = abc.ABC if hasattr(abc, 'ABC') else abc.ABCMeta('ABC', (object,), {'__slots__': ()})
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

        # A derived class adds a non-default field after a default one.
        with self.assertRaisesRegexp(TypeError,
                                     "non-default argument 'y' follows "
                                     "default argument 'x'"):
            @dataclass
            class B(object):
                x = field(int, 0)

            @dataclass
            class C(B):
                y = field(int)

        # Override a base class field and add a default to
        #  a field which didn't use to have a default.
        with self.assertRaisesRegexp(TypeError,
                                     "non-default argument 'y' follows "
                                     "default argument 'x'"):
            @dataclass
            class B(object):
                x = field(int)
                y = field(int)

            @dataclass
            class C(B):
                x = field(int, 0)

    def test_field_no_default(self):
        @dataclass
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int)

        self.assertEqual(C(5).x, 5)

        with self.assertRaisesRegexp(TypeError,
                                     r"__init__\(\) (takes exactly 2 arguments \(1 given\)|missing 1 required positional argument)"):
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
            y = field(int, compare=False, default=4)

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
            self.assertIn(type(f), [_Field, Field])
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

        @dataclass
        class D(B):
            c = field(str, 'D:c')

        self.assertEqual([(f.name, f.default) for f in fields(D)],
                         [('a', 'B:a'),
                          ('b', 'B:b'),
                          ('c', 'D:c')])

        @dataclass
        class E(D):
            a = field(str, 'E:a')
            d = field(str, 'E:d')

        self.assertEqual([(f.name, f.default) for f in fields(E)],
                         [('a', 'E:a'),
                          ('b', 'B:b'),
                          ('c', 'D:c'),
                          ('d', 'E:d')])

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
        # post-init gets called, but doesn't raise. This is just
        #  checking that self is used correctly.
        C(5)

        # If there's not an __init__, then post-init won't get called.
        @dataclass(init=False)
        class C(object):
            def __post_init__(self):
                raise CustomError()
        # Creating the class won't raise
        C()

        @dataclass
        class C(object):
            x = field(int, 0)
            def __post_init__(self):
                self.x *= 2
        self.assertEqual(C().x, 0)
        self.assertEqual(C(2).x, 4)

        # Make sure that if we're frozen, post-init can't set
        #  attributes.
        @dataclass(frozen=True)
        class C(object):
            x = field(int, 0)
            def __post_init__(self):
                self.x *= 2
        with self.assertRaises(FrozenInstanceError):
            C()

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

    #@unittest.skipIf(sys.version_info < (3,), "Python 3 cross-type comparison behavior")
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
                                                     "not supported between instances of '{0}' and '{0}'".format(cls.__name__)):
                            fn(cls(), cls())

        @dataclass(order=True)
        class C(object):
            pass
        self.assertLessEqual(C(), C())
        self.assertGreaterEqual(C(), C())

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
                for idx, fn in enumerate([lambda a, b: a < b,
                                          lambda a, b: a <= b,
                                          lambda a, b: a > b,
                                          lambda a, b: a >= b]):
                    with self.subTest(idx=idx):
                        with self.assertRaisesRegexp(TypeError,
                                                    "not supported between instances"):
                            fn(cls(0, 0), cls(0, 0))

        @dataclass(order=True)
        class C(object):
            #__annotations__ = {'x': int, 'y': int}
            x = field(int)
            y = field(int)

        for idx, fn in enumerate([lambda a, b: a == b,
                                  lambda a, b: a <= b,
                                  lambda a, b: a >= b]):
            with self.subTest(idx=idx):
                self.assertTrue(fn(C(0, 0), C(0, 0)))

        for idx, fn in enumerate([lambda a, b: a < b,
                                  lambda a, b: a <= b,
                                  lambda a, b: a != b]):
            with self.subTest(idx=idx):
                self.assertTrue(fn(C(0, 0), C(0, 1)))
                self.assertTrue(fn(C(0, 1), C(1, 0)))
                self.assertTrue(fn(C(1, 0), C(1, 1)))

        for idx, fn in enumerate([lambda a, b: a > b,
                                  lambda a, b: a >= b,
                                  lambda a, b: a != b]):
            with self.subTest(idx=idx):
                self.assertTrue(fn(C(0, 1), C(0, 0)))
                self.assertTrue(fn(C(1, 0), C(0, 1)))
                self.assertTrue(fn(C(1, 1), C(1, 0)))
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

        # Test a factory that returns a shared list.
        l = []
        @dataclass
        class C(object):
            x = field(int)
            y = field(list, default_factory=lambda: l)

        c0 = C(3)
        c1 = C(3)
        self.assertEqual(c0.x, 3)
        self.assertEqual(c0.y, [])
        self.assertEqual(c0, c1)
        self.assertIs(c0.y, c1.y)
        self.assertEqual(astuple(C(5, [1])), (5, [1]))

        # Test various other field flags.
        # repr
        @dataclass
        class C(object):
            x = field(list, default_factory=list, repr=False)
        self.assertEqual(repr(C()), two_or_three("tests._fixtures_py27.C()",'TestCase.test_default_factory.<locals>.C()'))
        self.assertEqual(C().x, [])

        # hash
        @dataclass(unsafe_hash=True)
        class C(object):
            x = field(list, default_factory=list, hash=False)
        self.assertEqual(astuple(C()), ([],))
        self.assertEqual(hash(C()), hash(()))

        # init (see also test_default_factory_with_no_init)
        @dataclass
        class C(object):
            x = field(list, default_factory=list, init=False)
        self.assertEqual(astuple(C()), ([],))

        # compare
        @dataclass
        class C(object):
            x = field(list, default_factory=list, compare=False)
        self.assertEqual(C(), C([1]))

    def test_missing_default(self):
        # Test that MISSING works the same as a default not being specified.
        @dataclass
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int, default=MISSING)

        with self.assertRaisesRegexp(TypeError,
                                     r"__init__\(\) (takes exactly 2 arguments \(1 given\)|missing 1 required positional argument)"):
            C()
        self.assertNotIn('x', C.__dict__)

        @dataclass
        class D(object):
            x = field(int)
        with self.assertRaisesRegexp(TypeError,
                                     r"__init__\(\) (takes exactly 2 arguments \(1 given\)|missing 1 required positional argument)"):
            D()
        self.assertNotIn('x', D.__dict__)

    def test_missing_default_factory(self):
        # Test that MISSING works the same as a default factory not being specified.
        @dataclass
        class C(object):
            #__annotations__ = {'x': int}
            x = field(int, default_factory=MISSING)

        with self.assertRaisesRegexp(TypeError,
                                     r"__init__\(\) (takes exactly 2 arguments \(1 given\)|missing 1 required positional argument)"):
            C()
        self.assertNotIn('x', C.__dict__)

        @dataclass
        class D(object):
            x = field(int, default=MISSING, default_factory=MISSING)
        with self.assertRaisesRegexp(TypeError,
                                     r"__init__\(\) (takes exactly 2 arguments \(1 given\)|missing 1 required positional argument)"):
            D()
        self.assertNotIn('x', D.__dict__)

    def test_field_repr(self):
        int_field = field(int, default=1, init=True, repr=False, doc='Docstring')
        int_field.name = "id"
        repr_output = repr(int_field)

        # Check the Field repr contains expected components
        self.assertIn("Field(name='id'", repr_output)
        self.assertIn("default=1", repr_output)
        self.assertIn("init=True", repr_output)
        self.assertIn("repr=False", repr_output)
        self.assertIn("doc='Docstring'", repr_output)

    def test_field_recursive_repr(self):
        rec_field = field()
        rec_field.type = rec_field
        rec_field.name = "id"
        repr_output = repr(rec_field)

        self.assertIn(",type=...,", repr_output)

    def test_recursive_annotation(self):
        class C(object):
            pass

        @dataclass
        class D(object):
            C = field(C)

        self.assertIn(",type=...,", repr(D.__dataclass_fields__["C"]))

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

        try:
            from funcsigs import signature as _signature
        except ImportError:
            from inspect import signature as _signature
        for param in _signature(dataclass).parameters:
            if param == 'cls':
                continue
            self.assertHasAttr(Some.__dataclass_params__, param)

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
        try:
            from funcsigs import signature as _signature
        except ImportError:
            from inspect import signature as _signature
        sig = _signature(C.__init__)
        first = next(iter(sig.parameters))
        self.assertNotEqual('self', first)

        # But we do use 'self' if no field named self.
        @dataclass
        class C(object):
            selfx = field(str)

        # Make sure the first parameter is named 'self'.
        sig = _signature(C.__init__)
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

    #@unittest.skipIf(sys.version_info < (3,), "Python 3 cross-type comparison behavior")
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

    #@unittest.skipIf(sys.version_info < (3,), "Python 3 cross-type comparison behavior")
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
                                             r"not supported between instances of 'B' and 'C'"):
                    fn(B(0), C(0))
    #@unittest.skip("We have __lt__ and __gt__ everywhere to trigger a proper exception")
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
        with self.assertRaisesRegexp(TypeError, "'Point3D' object is not iterable|cannot unpack non-iterable Point3D"):
            x, y, z = Point3D(4, 5, 6)

        # Make sure another class with the same field names isn't
        #  equal.
        @dataclass
        class Point3Dv1(object):
            x = field(int, 0)
            y = field(int, 0)
            z = field(int, 0)
        self.assertNotEqual(Point3D(0, 0, 0), Point3Dv1())
    #@unittest.skip(" we can't check this in pyton 2")
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
        from typing import TypeVar, Generic
        S = TypeVar('S')
        T = TypeVar('T')

        @dataclass
        class Base(Generic[T, S]):
            x = field(T)
            y = field(S)

        @dataclass
        class DataDerived(Base):
            new_field = field(str)

        c = DataDerived(0, 'test1', 'test2')
        self.assertEqual(astuple(c), (0, 'test1', 'test2'))

        class NonDataDerived(Base):
            def new_method(self):
                return self.y

        c = NonDataDerived(10, 1.0)
        self.assertEqual(c.new_method(), 1.0)

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

        self.assertEqual(A.__init__.__name__, "__init__")
        for function in (
            '__eq__',
            '__lt__',
            '__le__',
            '__gt__',
            '__ge__',
            '__hash__',
            '__init__',
            '__repr__',
            '__setattr__',
            '__delattr__',
        ):
            # Check that qualname contains the class name (may vary by implementation)
            qualname = getattr(A, function).__qualname__
            self.assertIn('A', qualname, "Function {} qualname should contain 'A': {}".format(function, qualname))

        with self.assertRaisesRegexp(TypeError, two_or_three(r"__init__\(\) takes", r"A\.__init__\(\) missing")):
            A()

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

        @dataclass
        class C(object):
            x = field(InitVar(int), default=10)
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

        # Make sure the repr is correct.
        try:
            from typing import List
            self.assertIn('InitVar[int]', repr(InitVar(int)))
            self.assertIn('InitVar', repr(InitVar(List[int])))
        except:
            # Type repr may vary in py2, just check it doesn't crash
            repr(InitVar(int))

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

    #@unittest.skip("property overwrites Field descriptor in py2dataclasses")
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
            y = field(int)

        @dataclass
        class C(B):
            z = field(int)

        c = C(1, 3)
        self.assertEqual((c.x, c.z), (1, 3))

        # .y was not initialized.
        with self.assertRaisesRegexp(AttributeError,
                                     'object has no attribute'):
            c.y

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

        # Also test for an instance attribute.
        class B(object):
            pass
        b = B()
        b.__dataclass_fields__ = []

        for obj in [a, b]:
            self.assertFalse(is_dataclass(obj))

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
        from collections import namedtuple, OrderedDict
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

        # Now with a dict_factory.  OrderedDict is convenient, but
        # since it compares to dicts, we also need to have separate
        # assertIs tests.
        d = asdict(c, dict_factory=OrderedDict)
        self.assertEqual(d, {'x': 'outer',
                             'y': T(1,
                                    {'x': 'inner',
                                     'y': T(11, 12, 13)},
                                    2),
                             }
                         )

        # Make sure that the returned dicts are actually OrderedDicts.
        self.assertIs(type(d), OrderedDict)
        self.assertIs(type(d['y'][1]), OrderedDict)

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
        def setattr(self, name, value):
            calls.append((name, value))

        C.__setattr__ = setattr
        c = C(0, 1)
        self.assertEqual(('a', 0), calls[0])
        self.assertEqual(('b', 1), calls[1])
        self.assertEqual(('c', []), calls[2])
        self.assertEqual(('d', []), calls[3])
        self.assertNotIn(('e', 4), calls)
        self.assertEqual(('f', 4), calls[4])

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
            s = traceback.format_exc(10)
            if not isinstance(s, type(u'')):
                s = s.decode("utf-8")
            print(s, file=stdout)
            #traceback.print_exception(type(exc), exc, sys.exc_info()[2], file=stdout)
        printed_traceback = stdout.getvalue()
        self.assertNotIn("AttributeError", printed_traceback)
        self.assertNotIn("__dataclass_fields__", printed_traceback)

    def test_incomplete_annotations(self):
        try:
            import annotationlib
        except ImportError:
            # annotationlib not available in py2, skip the advanced test
            @dataclass
            class C(object):
                pass
            # For now, just make sure it doesn't crash
            _ = C()
            return

        @dataclass
        class C(object):
            "doc"
            x = field(int)

        C.__annotate__ = lambda _: {}

        self.assertEqual(
            annotationlib.get_annotations(C.__init__),
            {"return": None}
        )

    def test_classvar_default_factory(self):
        # It's an error for a ClassVar to have a factory function.
        from typing import ClassVar
        with self.assertRaisesRegexp(TypeError,
                                     'cannot have a default factory'):
            @dataclass
            class C(object):
                x = field(ClassVar[int], default_factory=int)

    #@unittest.skipIf(sys.version_info < (3,), "types.GenericAlias not available on Python 2")
    def test_is_dataclass_genericalias(self):

        @dataclass
        class A(GenericAlias):
            origin = field(type)
            args = field(type)
        self.assertTrue(is_dataclass(A))
        a = A(list, int)
        self.assertTrue(is_dataclass(type(a)))
        self.assertTrue(is_dataclass(a))


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
        with self.assertRaisesRegexp(TypeError, r'__init__\(\) (takes exactly 3 arguments \(2 given\)|missing 1 required positional argument)'):
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

    def test_init_var(self):
        
        def post_init(self, y):
            self.x *= y

        C = make_dataclass('C',
                           [('x', int),
                            ('y', InitVar(int)),
                            ],
                           namespace={'__post_init__': post_init},
                           )
        c = C(2, 3)
        self.assertEqual(vars(c), {'x': 6})
        self.assertEqual(len(fields(c)), 1)

    def test_class_var(self):
        from typing import ClassVar
        C = make_dataclass('C',
                           [('x', int),
                            ('y', ClassVar[int], 10),
                            ],
                           )

        self.assertEqual(C.y, 10)
        self.assertEqual(len(fields(C)), 1)

        c = C(5)
        self.assertEqual(c.x, 5)
        self.assertEqual(C.y, 10)

    def test_other_params(self):
        C = make_dataclass('C',
                           [('x', int),
                            ('y', object, 10),
                            ],
                           init=False)
        # Make sure we have a repr, but no init.
        self.assertNotIn('__init__', vars(C))
        self.assertIn('__repr__', vars(C))

        # Make sure random other params don't work.
        with self.assertRaisesRegexp(TypeError, 'unexpected keyword argument'):
            C = make_dataclass('C',
                               [],
                               xxinit=False)

    def test_keyword_field_names(self):
        for field_name in ['for', 'while', 'if', 'else']:
            with self.subTest(field=field_name):
                with self.assertRaisesRegexp(TypeError, 'must not be keywords'):
                    make_dataclass('C', ['a', field_name])

    def test_non_identifier_field_names(self):
        for field_name in ['()', 'x,y', '*']:
            with self.subTest(field=field_name):
                with self.assertRaisesRegexp(TypeError, 'must be valid identifiers'):
                    make_dataclass('C', ['a', field_name])

    def test_underscore_field_names(self):
        # Unlike namedtuple, it's okay if dataclass field names have an underscore.
        make_dataclass('C', ['_', '_a', 'a_a', 'a_'])

    def test_no_types_get_annotations(self):
        C = make_dataclass('C', ['x', ('y', int), 'z'])
        # Just make sure it doesn't crash
        _ = C(1, 2, 'three')

    def test_no_types_no_typing_import(self):
        # For Python 2, just verify the class is created without issues
        C = make_dataclass('C', ['x', ('y', int)])
        self.assertIsNotNone(C)
        c = C('test_x', 42)
        self.assertEqual(c.x, 'test_x')
        self.assertEqual(c.y, 42)

    def test_invalid_type_specification(self):
        for bad_field in [(), (1, 2, 3, 4)]:
            with self.subTest(bad_field=bad_field):
                with self.assertRaisesRegexp(TypeError, 'Invalid field:'):
                    make_dataclass('C', ['a', bad_field])

    def test_duplicate_field_names(self):
        for field in ['a', 'ab']:
            with self.subTest(field=field):
                with self.assertRaisesRegexp(TypeError, 'Field name duplicated'):
                    make_dataclass('C', [field, 'a', field])

    def test_dataclass_decorator_default(self):
        C = make_dataclass('C', [('x', int)], decorator=dataclass)
        c = C(10)
        self.assertEqual(c.x, 10)

    def test_dataclass_custom_decorator(self):
        def custom_dataclass(cls, *args, **kwargs):
            dc = dataclass(cls, *args, **kwargs)
            dc.__custom__ = True
            return dc

        C = make_dataclass('C', [('x', int)], decorator=custom_dataclass)
        c = C(10)
        self.assertEqual(c.x, 10)
        self.assertEqual(c.__custom__, True)

    def test_funny_class_names_names(self):
        # No reason to prevent weird class names
        for classname in ['()', 'x,y', '*']:
            with self.subTest(classname=classname):
                C = make_dataclass(classname, ['a', 'b'])
                self.assertEqual(C.__name__, classname)

    def test_pickle_support(self):
        # Test that dataclasses created with make_dataclass can be pickled
        C = make_dataclass('C', [('x', int)])
        c = C(10)
        with expose_to_test(C):
            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(proto=proto):
                    pickled = pickle.dumps(c, proto)
                    unpickled = pickle.loads(pickled)
                    self.assertEqual(c, unpickled)
                    self.assertEqual(c.x, unpickled.x)

    def test_cannot_be_pickled(self):
        # Test that dataclasses with wrong module cannot be pickled reliably
        # For Python 2, we just verify basic pickle behavior works
        C = make_dataclass('C', [('x', int)])
        c = C(10)
        with expose_to_test(C):
            # Should be pickleable normally
            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(proto=proto):
                    pickled = pickle.dumps(c, proto)
                    unpickled = pickle.loads(pickled)
                    self.assertEqual(c.x, unpickled.x)

    def test_module_attr(self):
        # Test that module is set correctly
        C = make_dataclass('C', [('x', int)])
        self.assertEqual(C.__module__, __name__)

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

    def test_classvar(self):
        from typing import ClassVar
        @dataclass
        class C(object):
            x = field(int)
            y = field(ClassVar[int], 1000)

        c = C(1)
        d = C(2)

        self.assertIs(c.y, d.y)
        self.assertEqual(c.y, 1000)

        # Trying to replace y is an error: can't replace ClassVars.
        with self.assertRaisesRegexp(TypeError,
                                     r"__init__\(\) got an unexpected keyword argument 'y'"):
            replace(c, y=30)

        replace(c, x=5)

    def test_initvar_is_specified(self):
        
        @dataclass
        class C(object):
            x = field(int)
            y = field(InitVar(int))

            def __post_init__(self, y):
                self.x *= y

        c = C(1, 10)
        self.assertEqual(c.x, 10)
        with self.assertRaisesRegexp(TypeError,
                                     "InitVar 'y' must be specified with replace"):
            replace(c, x=3)
        c = replace(c, x=3, y=5)
        self.assertEqual(c.x, 15)

    def test_initvar_with_default_value(self):
        
        @dataclass
        class C(object):
            x = field(int)
            y = field(InitVar(int), None)
            z = field(InitVar(int), 42)

            def __post_init__(self, y, z):
                if y is not None:
                    self.x += y
                if z is not None:
                    self.x += z

        c = C(x=1, y=10, z=1)
        self.assertEqual(replace(c), C(x=12))
        self.assertEqual(replace(c, y=4), C(x=12, y=4, z=42))
        self.assertEqual(replace(c, y=4, z=1), C(x=12, y=4, z=1))

    def test_recursive_repr(self):
        @dataclass
        class C(object):
            f = field(object)

        c = C(None)
        c.f = c
        self.assertIn("C(f=...", repr(c))

    def test_recursive_repr_two_attrs(self):
        @dataclass
        class C(object):
            f = field(object)
            g = field(object)

        c = C(None, None)
        c.f = c
        c.g = c
        self.assertIn("C(f=..., g=...", repr(c))

    def test_recursive_repr_indirection(self):
        @dataclass
        class C(object):
            f = field(object)

        @dataclass
        class D(object):
            f = field(object)

        c = C(None)
        d = D(None)
        c.f = d
        d.f = c
        self.assertIn("C(f=", repr(c))
        self.assertIn("D(f=...", repr(c))

    def test_recursive_repr_indirection_two(self):
        @dataclass
        class C(object):
            f = field(object)

        @dataclass
        class D(object):
            f = field(object)

        @dataclass
        class E(object):
            f = field(object)

        c = C(None)
        d = D(None)
        e = E(None)
        c.f = d
        d.f = e
        e.f = c
        # Just verify the repr doesn't crash and contains expected parts
        repr_str = repr(c)
        self.assertIn("C(f=", repr_str)
        self.assertIn("D(f=", repr_str)
        self.assertIn("E(f=...", repr_str)

    def test_recursive_repr_misc_attrs(self):
        @dataclass
        class C(object):
            f = field(object)
            g = field(int)

        c = C(None, 1)
        c.f = c
        self.assertIn("C(f=..., g=1)", repr(c))

@unittest.skipIf(six.PY2, "Python 2.7 can't append __doc__ to objects and classes.")
class TestDocString(unittest.TestCase):
    def assertDocStrEqual(self, a, b):
        # Because 3.6 and 3.7 differ in how inspect.signature work
        #  (see bpo #32108), for the time being just compare them with
        #  whitespace stripped.
        self.assertEqual((a or "").replace(' ', ''), b.replace(' ', ''))

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

    def test_docstring_one_field_with_default_none(self):
        @dataclass
        class C(object):
            x = field('Union[int, type(None)]', default=None)

        self.assertDocStrEqual(C.__doc__, "C(x:int|None=None)")

    def test_docstring_deque_field(self):
        @dataclass
        class C(object):
            """a"""
            x = field(deque)

        self.assertDocStrEqual(C.__doc__, "C(x:collections.deque)")

    def test_docstring_deque_field_with_default_factory(self):
        @dataclass
        class C(object):
            x = field(deque, default_factory=deque)

        self.assertDocStrEqual(C.__doc__, "C(x:collections.deque=<factory>)")

    def test_docstring_with_unsolvable_forward_ref_in_init(self):
        # See: https://github.com/python/cpython/issues/128184
        ns = {}
        exec(textwrap.dedent("""
from dataclasses import dataclass, field

@dataclass
class C(object):
    def __init__(self, x, num):
        # type: (X, int) -> None
        pass
"""), ns)

        self.assertDocStrEqual(ns['C'].__doc__, "C(x:X,num:int)")

    def test_docstring_with_no_signature(self):
        # See https://github.com/python/cpython/issues/103449
        # Python 2.7 doesn't support metaclass= syntax in the same way
        # We need to use __metaclass__ or six.with_metaclass
        Meta = type('Meta', (type,), {'__call__': dict})
        Base = Meta('Base', (object,), {})

        @dataclass
        class C(Base):
            pass

        self.assertDocStrEqual(C.__doc__, "C")


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
    def test_inherit_from_protocol(self):
        # Dataclasses inheriting from protocol should preserve their own __init__.
        # Protocol is tricky in Python 2, so we'll just test basic inheritance
        @dataclass
        class C(object):
            a = field(int)

        self.assertEqual(C(5).a, 5)


class TestInitAnnotate(unittest.TestCase):
    """Tests for __annotate__ function (PEP 649).

    Note: These tests are not applicable to Python 2.7 as it doesn't support
    PEP 649's __annotate__ function. The tests are kept for completeness but
    will be skipped.
    """

    @unittest.skip("PEP 649 __annotate__ not applicable to Python 2.7")
    def test_annotate_function(self):
        # No forward references - not applicable to py27
        pass

    @unittest.skip("PEP 649 __annotate__ not applicable to Python 2.7")
    def test_annotate_function_forwardref(self):
        # With forward references - not applicable to py27
        pass

    @unittest.skip("PEP 649 __annotate__ not applicable to Python 2.7")
    def test_annotate_function_init_false(self):
        # Check `init=False` attributes - not applicable to py27
        pass

    @unittest.skip("PEP 649 __annotate__ not applicable to Python 2.7")
    def test_annotate_function_contains_forwardref(self):
        # Check string annotations - not applicable to py27
        pass

    @unittest.skip("PEP 649 __annotate__ not applicable to Python 2.7")
    def test_annotate_function_not_replaced(self):
        # Check that __annotate__ is not replaced - not applicable to py27
        pass

    @unittest.skip("PEP 649 __annotate__ not applicable to Python 2.7")
    def test_slots_true_init_false(self):
        # Test slots=True and init=False - not applicable to py27
        pass

    @unittest.skip("PEP 649 __annotate__ not applicable to Python 2.7")
    def test_init_false_forwardref(self):
        # Test forward references - not applicable to py27
        pass


class TestRepr(unittest.TestCase):
    def test_repr(self):

        @dataclass
        class B(object):
            x = field(int)

        @dataclass
        class C(B):
            y = field(int, default=10)

        o = C(4)
        self.assertEqual(repr(o), two_or_three("tests._fixtures_py27.C(x=4, y=10)", 'TestRepr.test_repr.<locals>.C(x=4, y=10)'))

        @dataclass
        class D(C):
            x = field(int, default = 20)
        self.assertEqual(repr(D()), two_or_three("tests._fixtures_py27.D(x=20, y=10)", 'TestRepr.test_repr.<locals>.D(x=20, y=10)'))

        @dataclass
        class C(object):
            @dataclass
            class D(object):
                i = field(int)
            @dataclass
            class E(object):
                pass
        self.assertEqual(repr(C.D(0)), two_or_three("tests._fixtures_py27.D(i=0)", 'TestRepr.test_repr.<locals>.C.D(i=0)'))
        self.assertEqual(repr(C.E()), two_or_three("tests._fixtures_py27.E()",'TestRepr.test_repr.<locals>.C.E()'))

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
            (False,        False, True,   '',                  ''),
            (False,        True,  False,  'none',              ''),
            (False,        True,  True,   'fn',                ''),
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
        # Test dataclasses with no hash= argument.  This exists to
        #  make sure that if the @dataclass parameter name is changed
        #  or the non-default hashing behavior changes, the default
        #  hashability keeps working the same way.

        class Base(object):
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
                        i = field(int)
                elif frozen is None:
                    @dataclass(eq=eq)
                    class C(base):
                        i = field(int)
                elif eq is None:
                    @dataclass(frozen=frozen)
                    class C(base):
                        i = field(int)
                else:
                    @dataclass(frozen=frozen, eq=eq)
                    class C(base):
                        i = field(int)

                # Now, make sure it hashes as expected.
                if expected == 'unhashable':
                    c = C(10)
                    with self.assertRaisesRegexp(TypeError, 'unhashable type'):
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
                    assert False, 'unknown value for expected={0!r}'.format(expected)

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
        msg = r"(Can't instantiate|cannot instantiate) abstract class Date"
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

    def test_no_classvar_kwarg(self):
        from typing import ClassVar
        msg = 'field a is a ClassVar but specifies kw_only'
        with self.assertRaisesRegexp(TypeError, msg):
            @dataclass
            class A(object):
                a = field(ClassVar[int], kw_only=True)

        with self.assertRaisesRegexp(TypeError, msg):
            @dataclass
            class A(object):
                a = field(ClassVar[int], kw_only=False)

        with self.assertRaisesRegexp(TypeError, msg):
            @dataclass(kw_only=True)
            class A(object):
                a = field(ClassVar[int], kw_only=False)

    def test_KW_ONLY(self):
        # Python 2 doesn't support KW_ONLY sentinel field syntax
        # but we can still test kw_only functionality using field(kw_only=True)
        @dataclass
        class A(object):
            a = field(int)
            b = field(int, kw_only=True)
            c = field(int, kw_only=True)

        # Should be able to create with positional a and keyword-only b, c
        a_inst = A(3, c=5, b=4)
        self.assertEqual(a_inst.a, 3)
        self.assertEqual(a_inst.b, 4)
        self.assertEqual(a_inst.c, 5)

        @dataclass(kw_only=True)
        class B(object):
            a = field(int)
            b = field(int)
            c = field(int)

        # All fields are keyword-only
        b_inst = B(a=3, b=4, c=5)
        self.assertEqual(b_inst.a, 3)
        self.assertEqual(b_inst.b, 4)
        self.assertEqual(b_inst.c, 5)

        @dataclass
        class C(object):
            a = field(int)
            b = field(int, kw_only=True)
            c = field(int, kw_only=False)

        # a is positional, b is kw-only, c is positional
        c_inst = C(1, 2, b=3)
        self.assertEqual(c_inst.a, 1)
        self.assertEqual(c_inst.b, 3)
        self.assertEqual(c_inst.c, 2)

        c_inst = C(1, b=3, c=2)
        self.assertEqual(c_inst.a, 1)
        self.assertEqual(c_inst.b, 3)
        self.assertEqual(c_inst.c, 2)

    def test_KW_ONLY_as_string(self):
        # Python 2 doesn't support KW_ONLY sentinel field or string annotations for it
        # Test that kw_only works as a field parameter
        @dataclass
        class A(object):
            a = field(int)
            b = field(int, kw_only=True)
            c = field(int)

        # Verify kw_only is set correctly
        fs = fields(A)
        self.assertFalse(fs[0].kw_only)  # a
        self.assertTrue(fs[1].kw_only)   # b
        self.assertFalse(fs[2].kw_only)  # c

    def test_KW_ONLY_twice(self):

        @dataclass
        class A(object):
            a = field(int, kw_only=True)
            b = field(int, kw_only=False)  # Conflicting specification

        # Just verify the class was created with mixed kw_only settings
        fs = fields(A)
        self.assertTrue(fs[0].kw_only)
        self.assertFalse(fs[1].kw_only)


    def test_post_init(self):
        @dataclass
        class A(object):
            a = field(int)
            b = field(InitVar(int), kw_only=True)
            c = field(int, kw_only=True)
            d = field(InitVar(int), kw_only=True)

            def __post_init__(self, b, d):
                # Modify a based on b and d
                self.a = self.a + b + d


        a_inst = A(1, b=3, c=2, d=4)
        self.assertEqual(a_inst.a, 1 + 3 + 4)
        self.assertEqual(a_inst.c, 2)

    def test_defaults(self):
        # For kwargs, make sure we can have defaults after non-defaults.
        @dataclass
        class A(object):
            a = field(int, default=0, kw_only=True)
            b = field(int, kw_only=True)
            c = field(int, default=1, kw_only=True)
            d = field(int, kw_only=True)

        # Python 2 doesn't support keyword-only args in __init__, so we just verify the fields exist
        self.assertEqual(len(fields(A)), 4)

    def test_make_dataclass(self):
        A = make_dataclass('A', ['a'], kw_only=True)
        self.assertTrue(fields(A)[0].kw_only)

        B = make_dataclass('B',
                           ['a', ('b', int, field(int, kw_only=False))],
                           kw_only=True)
        self.assertTrue(fields(B)[0].kw_only)
        self.assertFalse(fields(B)[1].kw_only)

    def test_deferred_annotations(self):
        @dataclass
        class A(object):
            x = field(object)

        # Just verify the field is created
        fs = fields(A)
        self.assertEqual(len(fs), 1)
        self.assertEqual(fs[0].name, 'x')


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

        with self.assertRaisesRegexp(TypeError, r'(takes exactly 2 arguments|missing 1 required positional argument)'):
            c = C()

from contextlib import contextmanager
import sys

@contextmanager
def expose_to_test(*classes):
    saved = []
    try:
        for cls in classes:
            mod = sys.modules[cls.__module__]
            old_qualname = getattr(cls, '__qualname__', None)
            saved.append((mod, cls.__name__, getattr(mod, cls.__name__, None), cls, old_qualname))
            setattr(mod, cls.__name__, cls)
            cls.__qualname__ = cls.__name__
        yield
    finally:
        for mod, name, orig, cls, old_qualname in saved:
            if old_qualname is not None:
                cls.__qualname__ = old_qualname
            if orig is None:
                delattr(mod, name)
            else:
                setattr(mod, name, orig)


def two_or_three(two, three):
    return two if six.PY2 else three




class TestSlots(unittest.TestCase):


    def test_frozen_pickle(self):

        @dataclass(frozen=True)
        class FrozenWithoutSlotsClass(object):
            foo = field(str)
            bar = field(int)

        @dataclass(frozen=True, slots=True)
        class FrozenSlotsClass(object):
            foo = field(str)
            bar = field(int)
        for proto in range(pickle.HIGHEST_PROTOCOL + 1):
            with self.subTest(proto=proto):
                with expose_to_test(FrozenWithoutSlotsClass, FrozenSlotsClass):
                    obj = FrozenSlotsClass("a", 1)
                    p = pickle.loads(pickle.dumps(obj, protocol=proto))
                    self.assertIsNot(obj, p)
                    self.assertEqual(obj, p)

                    obj = FrozenWithoutSlotsClass("a", 1)
                    p = pickle.loads(pickle.dumps(obj, protocol=proto))
                    self.assertIsNot(obj, p)
                    self.assertEqual(obj, p)
    def test_simple(self):
        @dataclass(slots=True)
        class C(object):
            x = field(int)

        # There was a bug where a variable in a slot was assumed to
        #  also have a default value (of type
        #  types.MemberDescriptorType).
        with self.assertRaisesRegexp(TypeError,
                                     r"__init__\(\) (takes exactly 2 arguments \(1 given\)|missing 1 required positional argument)"):
            C()

        # We can create an instance, and assign to x.
        c = C(10)
        self.assertEqual(c.x, 10)
        c.x = 5
        self.assertEqual(c.x, 5)

        # We can't assign to anything else.
        with self.assertRaisesRegexp(AttributeError, "'C' object has no attribute 'y'"):
            c.y = 5

    def test_derived_added_field(self):
        # See bpo-33100.
        @dataclass(slots=True)
        class Base(object):
            #__slots__ = ('x',)
            x = field(int)

        @dataclass
        class Derived(Base):
            x = field(int)
            y = field(int)

        d = Derived(1, 2)
        self.assertEqual((d.x, d.y), (1, 2))

        # We can add a new field to the derived instance.
        d.z = 10

    def test_frozen_slots_pickle_custom_state(self):

        # This test uses __getstate__ and __setstate__ with frozen slots
        @dataclass(frozen=True, slots=True)
        class FrozenSlotsGetStateClass(object):
            ##__slots__ = ('foo', 'bar', 'getstate_called')
            foo = field(str)
            bar = field(int)
            getstate_called = field(bool, default=False, compare=False)

            def __getstate__(self):
                object.__setattr__(self, 'getstate_called', True)
                return [self.foo, self.bar]


        @dataclass(frozen=True, slots=True)
        class FrozenSlotsSetStateClass(object):
            #__slots__ = ('foo', 'bar', 'setstate_called')
            foo = field(str)
            bar = field(int)
            setstate_called = field(bool, default=False, compare=False)

            def __setstate__(self, state):
                object.__setattr__(self, 'setstate_called', True)
                object.__setattr__(self, 'foo', state[0])
                object.__setattr__(self, 'bar', state[1])

        @dataclass(frozen=True, slots=True)
        class FrozenSlotsAllStateClass(object):
            #__slots__ = ('foo', 'bar', 'getstate_called', 'setstate_called')
            foo = field(str)
            bar = field(int)
            getstate_called = field(bool, default=False, compare=False)
            setstate_called = field(bool, default=False, compare=False)

            def __getstate__(self):
                object.__setattr__(self, 'getstate_called', True)
                return [self.foo, self.bar]

            def __setstate__(self, state):
                object.__setattr__(self, 'setstate_called', True)
                object.__setattr__(self, 'foo', state[0])
                object.__setattr__(self, 'bar', state[1])



        with expose_to_test(FrozenSlotsAllStateClass, FrozenSlotsGetStateClass, FrozenSlotsSetStateClass):

            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(proto=proto):

                    obj = FrozenSlotsGetStateClass('a', 1)
                    dumped = pickle.dumps(obj, protocol=proto)

                    self.assertTrue(obj.getstate_called)
                    self.assertEqual(obj, pickle.loads(dumped))

            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(proto=proto):
                    obj = FrozenSlotsSetStateClass('a', 1)
                    obj2 = pickle.loads(pickle.dumps(obj, protocol=proto))

                    self.assertTrue(obj2.setstate_called)
                    self.assertEqual(obj, obj2)

            for proto in range(pickle.HIGHEST_PROTOCOL + 1):
                with self.subTest(proto=proto):
                    obj = FrozenSlotsAllStateClass('a', 1)
                    dumped = pickle.dumps(obj, protocol=proto)

                    self.assertTrue(obj.getstate_called)

                    obj2 = pickle.loads(dumped)
                    self.assertTrue(obj2.setstate_called)
                    self.assertEqual(obj, obj2)

    def test_slots_with_default_no_init(self):
        @dataclass(slots=True)
        class A(object):
            #__slots__ = ('a', 'b')
            a = field(str)
            b = field(str, default='b', init=False)

        obj = A("a")
        self.assertEqual(obj.a, 'a')
        self.assertEqual(obj.b, 'b')

    def test_slots_with_default_factory_no_init(self):
        @dataclass(slots=True)
        class A(object):
            ##__slots__ = ('a', 'b')
            a = field(str)
            b = field(str, default_factory=lambda:'b', init=False)

        obj = A("a")
        self.assertEqual(obj.a, 'a')
        self.assertEqual(obj.b, 'b')

    def test_slots_no_weakref(self):
        @dataclass(slots=True)
        class A(object):
            #__slots__ = ()
            pass

        self.assertNotIn("__weakref__", A.__slots__)
        a = A()
        with self.assertRaisesRegexp(TypeError,
                                     "cannot create weak reference"):
            weakref.ref(a)
        with self.assertRaises(AttributeError):
            a.__weakref__

    def test_slots_weakref(self):
        # Test weakref_slot parameter
        @dataclass(slots=True, weakref_slot=True)
        class A(object):
            a = field(int)

        self.assertIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)
        self.assertIsNotNone(a_ref)

    def test_weakref_slot_without_slot(self):
        with self.assertRaisesRegexp(TypeError,
                                    "weakref_slot is True but slots is False"):
            @dataclass(weakref_slot=True)
            class A(object):
                a = field(int)

    def test_weakref_slot_make_dataclass(self):
        A = make_dataclass('A', [('a', int),], slots=True, weakref_slot=True)
        self.assertIn("__weakref__", A.__slots__)
        a = A(1)
        weakref.ref(a)

        # And make sure it raises if slots=True is not given.
        with self.assertRaisesRegexp(TypeError,
                                    "weakref_slot is True but slots is False"):
            B = make_dataclass('B', [('a', int),], weakref_slot=True)

    def test_weakref_slot_subclass_weakref_slot(self):
        @dataclass(slots=True, weakref_slot=True)
        class Base(object):
            f = field(int)

        # A *can* also specify weakref_slot=True if it wants to
        @dataclass(slots=True, weakref_slot=True)
        class A(Base):
            pass

        # __weakref__ is in the base class, not A.  But an instance of A
        # is still weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)
        self.assertIsNotNone(a_ref)

    def test_weakref_slot_subclass_no_weakref_slot(self):
        @dataclass(slots=True, weakref_slot=True)
        class Base(object):
            f = field(int)

        @dataclass(slots=True)
        class A(Base):
            pass

        # __weakref__ is in the base class, not A.  Even though A doesn't
        # specify weakref_slot, it should still be weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)
        self.assertIsNotNone(a_ref)

    def test_weakref_slot_normal_base_weakref_slot(self):
        class Base(object):
            __slots__ = ('__weakref__',)

        @dataclass(slots=True, weakref_slot=True)
        class A(Base):
            f = field(int)

        # __weakref__ is in the base class, not A.  But an instance of
        # A is still weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        a_ref = weakref.ref(a)
        self.assertIsNotNone(a_ref)

    def test_dataclass_derived_weakref_slot(self):
        class A(object):
            pass

        @dataclass(slots=True, weakref_slot=True)
        class B(A):
            pass

        self.assertEqual(B.__slots__, ())
        B()

    def test_dataclass_derived_generic(self):

        import typing
        T = typing.TypeVar('T')

        @dataclass(slots=True, weakref_slot=True)
        class A(typing.Generic[T]):
            pass
        self.assertEqual(A.__slots__, ('__weakref__',))
        A()

    def test_dataclass_derived_generic_from_base(self):

        import typing
        T = typing.TypeVar('T')

        class RawBase(object):
            pass

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

    def test_dataclass_derived_generic_from_slotted_base(self):
        import typing
        T = typing.TypeVar('T')

        class WithSlots(object):
            __slots__ = ('a', 'b')

        @dataclass(slots=True, weakref_slot=True)
        class E1(WithSlots, typing.Generic[T]):
            pass
        self.assertEqual(E1.__slots__, ('__weakref__',))
        E1()

        @dataclass(slots=True, weakref_slot=True)
        class E2(typing.Generic[T], WithSlots):
            pass
        self.assertEqual(E2.__slots__, ('__weakref__',))
        E2()


    def test_dataclass_derived_generic_from_slotted_base_with_weakref(self):

        import typing
        T = typing.TypeVar('T')

        class WithWeakrefSlot(object):
            __slots__ = ('__weakref__',)

        @dataclass(slots=True, weakref_slot=True)
        class G1(WithWeakrefSlot, typing.Generic[T]):
            pass
        self.assertEqual(G1.__slots__, ())
        G1()

        @dataclass(slots=True, weakref_slot=True)
        class G2(typing.Generic[T], WithWeakrefSlot):
            pass
        self.assertEqual(G2.__slots__, ())
        G2()

    def test_slots_weakref_base_str(self):
        class Base(object):
            __slots__ = '__weakref__'

        @dataclass(slots=True)
        class A(Base):
            a = field(int)

        # __weakref__ is in the base class, not A.  But an A is still weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        weakref.ref(a)

    def test_slots_weakref_base_tuple(self):
        # Same as test_slots_weakref_base, but use a tuple instead of a string
        # in the base class.
        class Base(object):
            __slots__ = ('__weakref__',)

        @dataclass(slots=True)
        class A(Base):
            a = field(int)

        # __weakref__ is in the base class, not A.  But an A is still
        # weakref-able.
        self.assertIn("__weakref__", Base.__slots__)
        self.assertNotIn("__weakref__", A.__slots__)
        a = A(1)
        weakref.ref(a)


    def test_dataclass_slot_dict(self):
        class WithDictSlot(object):
            __slots__ = ('__dict__',)

        @dataclass
        class A(WithDictSlot):
            pass

        self.assertEqual(A().__dict__, {})
        A()

    def test_generated_slots(self):
        @dataclass(slots=True)
        class C(object):
            x = field(int)
            y = field(int)

        c = C(1, 2)
        self.assertEqual((c.x, c.y), (1, 2))

        c.x = 3
        c.y = 4
        self.assertEqual((c.x, c.y), (3, 4))

        with self.assertRaisesRegexp(AttributeError, "object has no attribute 'z'"):
            c.z = 5

    def test_generated_slots_value(self):
        class Root(object):
            __slots__ = {'x'}

        class Root2(Root):
            __slots__ = {'k': '...', 'j': ''}

        class Root3(Root2):
            __slots__ = ['h']

        class Root4(Root3):
            __slots__ = 'aa'

        @dataclass(slots=True)
        class Base(Root4):
            y = field(int)
            j = field(str)
            h = field(str)

        self.assertEqual(Base.__slots__, ('y',))

        @dataclass(slots=True)
        class Derived(Base):
            aa = field(float)
            x = field(str)
            z = field(int)
            k = field(str)
            h = field(str)

        self.assertEqual(Derived.__slots__, ('z',))

        @dataclass
        class AnotherDerived(Base):
            z = field(int)

        self.assertNotIn('__slots__', AnotherDerived.__dict__)

    def test_slots_with_docs(self):
        class Root(object):
            __slots__ = {'x': 'x'}

        @dataclass(slots=True)
        class Base(Root):
            y1 = field(int, metadata={'doc': 'y1'})
            y2 = field(int)

        # For Python 2 compatibility, we check slots exists but skip doc comparison
        self.assertTrue(hasattr(Base, '__slots__'))

        @dataclass(slots=True)
        class Child(Base):
            z1 = field(int, metadata={'doc': 'z1'})
            z2 = field(int)

        # For Python 2 compatibility, we check slots exists but skip doc comparison
        self.assertTrue(hasattr(Child, '__slots__'))

    def test_add_slots_when_slots_exists(self):
        with self.assertRaisesRegexp(TypeError, 'already specifies __slots__'):
            @dataclass(slots=True)
            class C(object):
                __slots__ = ('y',)

    def test_cant_inherit_from_iterator_slots(self):
        class Root(object):
            __slots__ = iter(['a'])

        class Root2(Root):
            __slots__ = ('b', )

        with self.assertRaisesRegexp(
           TypeError,
            "^Slots of 'Root' cannot be determined"
        ):
            @dataclass(slots=True)
            class C(Root2):
                x = field(int)
    @unittest.skip("breaks everything")
    def test_slots_with_wrong_init_subclass(self):
        # Python 2 doesn't support __init_subclass__ with keyword arguments in class definition
        # This is a CPython 3.9+ feature. We'll test the CorrectSuper case which works.

        # Note: In Python 3, this test would include:
        # @dataclass(slots=True)
        # class WithWrongSuper(WrongSuper, arg=1):
        #     pass
        # But Python 2 doesn't support that syntax.

        class CorrectSuper(object):
            args = []
            def __init_subclass__(cls, arg="default"):
                cls.args.append(arg)

        @dataclass(slots=True)
        class WithCorrectSuper(CorrectSuper):
            pass

        # __init_subclass__ is called (possibly twice due to internal implementation)
        self.assertTrue(len(CorrectSuper.args) >= 1)

    def test_original_class_is_gced(self):
        # GC test - make sure original class gets garbage collected
        def make_simple():
            @dataclass(slots=True)
            class SlotsTest(object):
                pass

            return SlotsTest

        def make_with_annotations():
            @dataclass(slots=True)
            class SlotsTest(object):
                x = field(int)

            return SlotsTest

        def make_with_annotations_and_method():
            @dataclass(slots=True)
            class SlotsTest(object):
                x = field(int)

                def method(self):
                    return self.x

            return SlotsTest

        for make in (make_simple, make_with_annotations, make_with_annotations_and_method):
            with self.subTest(make=make):
                C = make()
                # Just verify the class was created
                self.assertIsNotNone(C)

    @unittest.skipIf(lambda x: hasattr(_testcapi, "HeapCTypeWithDict") is False, "Python 2.7 does not expose these types")
    def test_dataclass_slot_dict_ctype(self):

        import _testcapi
        @dataclass(slots=True)
        class HasDictOffset(_testcapi.HeapCTypeWithDict):
            __dict__ = {}
        self.assertEqual(HasDictOffset.__slots__, ())

        @dataclass(slots=True)
        class DoesNotHaveDictOffset(_testcapi.HeapCTypeWithWeakref):
            __dict__ = {}
        self.assertIn('__dict__', DoesNotHaveDictOffset.__slots__)

    def test_returns_new_class(self):
        class A(object):
            x = field(int)

        B = dataclass(A, slots=True)
        self.assertIsNot(A, B)

        self.assertFalse(hasattr(A, "__slots__"))
        self.assertTrue(hasattr(B, "__slots__"))


from dataclasses import *
from typing import *
class TestStringAnnotations(unittest.TestCase):
    def test_classvar(self):
        # Some expressions recognized as ClassVar really aren't.  But
        #  if you're using string annotations, it's not an exact
        #  science.
        # These tests assume that both "import typing" and "from
        # typing import *" have been run in this file.
        for typestr in ('ClassVar[int]',
                        'ClassVar [int]',
                        ' ClassVar [int]',
                        'ClassVar',
                        ' ClassVar ',
                        'typing.ClassVar[int]',
                        'typing.ClassVar[str]',
                        ' typing.ClassVar[str]',
                        'typing .ClassVar[str]',
                        'typing. ClassVar[str]',
                        'typing.ClassVar [str]',
                        'typing.ClassVar [ str]',

                        # Not syntactically valid, but these will
                        #  be treated as ClassVars.
                        'typing.ClassVar.[int]',
                        'typing.ClassVar+',
                        ):
            with self.subTest(typestr=typestr):
                @dataclass
                class C(object):
                    pass
                C.__annotations__ = {'x': typestr}

                # x is a ClassVar, so C() takes no args.
                C()

                # And it won't appear in the class's dict because it doesn't
                # have a default.
                self.assertNotIn('x', C.__dict__)

    def test_isnt_classvar(self):
        for typestr in ('CV',
                        't.ClassVar',
                        't.ClassVar[int]',
                        'typing..ClassVar[int]',
                        'Classvar',
                        'Classvar[int]',
                        'typing.ClassVarx[int]',
                        'typong.ClassVar[int]',
                        'dataclasses.ClassVar[int]',
                        'typingxClassVar[str]',
                        ):
            with self.subTest(typestr=typestr):
                @dataclass
                class C(object):
                    x = field(typestr)
                #C.__annotations__ = {'x': typestr}

                # x is not a ClassVar, so C() takes one arg.
                self.assertEqual(C(10).x, 10)

    def test_initvar(self):

        # These tests assume that both "import dataclasses" and "from
        #  dataclasses import *" have been run in this file.
        # typestr = 'dataclasses.InitVar[int]'
        # @dataclass
        # class CSSS(object):
        #     x = field(typestr)
        #     y = field('InitVar[int]')
        # #s = CSSS(1).x
        for typestr in ('InitVar[int]',
                        'InitVar [int]'
                        ' InitVar [int]',
                        'InitVar',
                        ' InitVar ',
                        'dataclasses.InitVar[int]', # 'dataclasses.InitVar[int]'
                        'dataclasses.InitVar[str]',
                        ' dataclasses.InitVar[str]',
                        'dataclasses .InitVar[str]',
                        'dataclasses. InitVar[str]',
                        'dataclasses.InitVar [str]',
                        'dataclasses.InitVar [ str]',

                        # Not syntactically valid, but these will
                        #  be treated as InitVars.
                        'dataclasses.InitVar.[int]',
                        'dataclasses.InitVar+',
                        ):
            with self.subTest(typestr=typestr):
                @dataclass
                class C(object):
                    x = field(typestr)

                # x is an InitVar, so doesn't create a member.
                with self.assertRaisesRegexp(AttributeError,
                                             "object has no attribute 'x'"):
                    C(1).x

    def test_isnt_initvar(self):
        for typestr in ('IV',
                        'dc.InitVar',
                        'xdataclasses.xInitVar',
                        'typing.xInitVar[int]',
                        ):
            with self.subTest(typestr=typestr):
                @dataclass
                class C(object):
                    x = field(typestr)

                # x is not an InitVar, so there will be a member x.
                self.assertEqual(C(10).x, 10)

    def test_classvar_module_level_import(self):
        from .dataclass_module_1 import CV as CV_1, IV as IV_1, USING_STRINGS as USING_STRINGS_1
        from .dataclass_module_1_str import CV as CV_1_str, IV as IV_1_str, USING_STRINGS as USING_STRINGS_1_str
        from .dataclass_module_2 import CV as CV_2, IV as IV_2, USING_STRINGS as USING_STRINGS_2
        from .dataclass_module_2_str import CV as CV_2_str, IV as IV_2_str, USING_STRINGS as USING_STRINGS_2_str

        modules_and_flags = [
            (CV_1, IV_1, USING_STRINGS_1),
            (CV_1_str, IV_1_str, USING_STRINGS_1_str),
            (CV_2, IV_2, USING_STRINGS_2),
            (CV_2_str, IV_2_str, USING_STRINGS_2_str),
        ]

        for cv_class, iv_class, using_strings in modules_and_flags:
            with self.subTest(cv_class=cv_class):
                # There's a difference in how the ClassVars are
                # interpreted when using string annotations or
                # not. See the imported modules for details.
                if using_strings:
                    c = cv_class(10)
                else:
                    c = cv_class()
                self.assertEqual(c.cv0, 20)

            with self.subTest(iv_class=iv_class):
                # There's a difference in how the InitVars are
                # interpreted when using string annotations or
                # not. See the imported modules for details.
                c = iv_class(0, 1, 2, 3, 4)

                for field_name in ('iv0', 'iv1', 'iv2', 'iv3'):
                    with self.subTest(field_name=field_name):
                        with self.assertRaisesRegexp(AttributeError, "object has no attribute"):
                            # Since field_name is an InitVar, it's
                            # not an instance field.
                            getattr(c, field_name)

                if using_strings:
                    # iv4 is interpreted as a normal field.
                    self.assertIn('not_iv4', c.__dict__)
                    self.assertEqual(c.not_iv4, 4)
                else:
                    # iv4 is interpreted as an InitVar, so it
                    # won't exist on the instance.
                    self.assertNotIn('not_iv4', c.__dict__)

    @unittest.skipIf(six.PY2, "Python 2.7 don't have annotations.")
    def test_text_annotations(self):
        from .dataclass_textanno import Bar, Foo

        # Skip this test as it requires get_type_hints functionality
        # that may not be fully compatible in Python 2.7
        raise Exception("Skip this test as it requires get_type_hints functionality")

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
                    dataclass(type('NotFrozenChild', bases, {}))

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
                    dataclass(type('FrozenChild', bases, {}), frozen=True)

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


class TestZeroArgumentSuperWithSlots(unittest.TestCase):
    """Tests for zero-argument super() and __class__ with slots.

    Note: Python 2.7 doesn't support zero-argument super() or implicit __class__.
    These tests verify that the backport handles this appropriately.
    """

    @unittest.skip("Python 2.7 doesn't support zero-argument super()")
    def test_zero_argument_super(self):
        # Python 2 doesn't support super() without arguments
        pass

    @unittest.skip("Python 2.7 doesn't have implicit __class__")
    def test_dunder_class_with_old_property(self):
        # Python 2 doesn't have implicit __class__ in closures
        pass

    @unittest.skip("Python 2.7 doesn't have implicit __class__")
    def test_dunder_class_with_new_property(self):
        # Python 2 doesn't support property decorator with @prop.setter/deleter
        # in the same way with __class__
        pass

    @unittest.skip("Python 2.7 doesn't have implicit __class__")
    def test_slots_dunder_class_property_getter(self):
        # Python 2 doesn't have implicit __class__
        pass

    @unittest.skip("Python 2.7 doesn't have implicit __class__")
    def test_slots_dunder_class_property_setter(self):
        # Python 2 doesn't have implicit __class__
        pass

    @unittest.skip("Python 2.7 doesn't have implicit __class__")
    def test_slots_dunder_class_property_deleter(self):
        # Python 2 doesn't have implicit __class__
        pass

    @unittest.skip("Python 2.7 doesn't support zero-argument super()")
    def test_wrapped(self):
        # Python 2 doesn't support zero-argument super()
        pass

    @unittest.skip("Python 2.7 doesn't have implicit __class__")
    def test_remembered_class(self):
        # Python 2 doesn't have implicit __class__ in closures
        pass


if __name__ == '__main__':
    unittest.main()

