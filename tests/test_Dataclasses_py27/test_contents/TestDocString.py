from __future__ import print_function, absolute_import

from common import *

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

    def test_docstring_one_field_with_default_none(self):
        @dataclass
        class C(object):
            x = field(type(None), default=None)

        self.assertDocStrEqual(C.__doc__, "C(x:int|None=None)")

    def test_docstring_list_field(self):
        @dataclass
        class C(object):
            x = field(list)

        self.assertDocStrEqual(C.__doc__, "C(x:List[int])")

    def test_docstring_list_field_with_default_factory(self):
        @dataclass
        class C(object):
            x = field(list, default_factory=list)

        self.assertDocStrEqual(C.__doc__, "C(x:List[int]=<factory>)")

    def test_docstring_deque_field(self):
        from collections import deque
        @dataclass
        class C(object):
            x = field(deque)

        self.assertDocStrEqual(C.__doc__, "C(x:collections.deque)")

    def test_docstring_deque_field_with_default_factory(self):
        from collections import deque
        @dataclass
        class C(object):
            x = field(deque, default_factory=deque)

        self.assertDocStrEqual(C.__doc__, "C(x:collections.deque=<factory>)")

    def test_docstring_undefined_name(self):
        @dataclass
        class C(object):
            x = field('undef')

        self.assertDocStrEqual(C.__doc__, "C(x:undef)")

    def test_docstring_with_unsolvable_forward_ref_in_init(self):
        import textwrap
        ns = {}
        exec(textwrap.dedent("""
from py2dataclasses.dataclasses import dataclass

@dataclass
class C(object):
    def __init__(self, x, num):
        pass
"""), ns)

        self.assertDocStrEqual(ns['C'].__doc__, "C(x:X,num:int)")

    def test_docstring_with_no_signature(self):
        class Meta(type):
            __call__ = dict
        class Base(object):
            __metaclass__ = Meta
            pass

        @dataclass
        class C(Base):
            pass

        self.assertDocStrEqual(C.__doc__, "C")