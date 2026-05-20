from __future__ import print_function

import unittest

from dataclasses import dataclass, field


class TestFieldDescriptor(unittest.TestCase):

    def _bind_field_name(self, cls, name):
        field_obj = cls.__dict__[name]
        if field_obj.name is None:
            field_obj.__set_name__(cls, name)
        return field_obj

    def test_uninitialized_inherited_field_descriptor_raises_attribute_error(self):
        @dataclass
        class A(object):
            x = field(int)

        class B(A):
            y = field(int)

        self._bind_field_name(B, 'y')

        @dataclass
        class C(B):
            z = field(int)

        c = C(1, 3)

        with self.assertRaises(AttributeError):
            c.y

    def test_falsey_instance_reads_field_default(self):
        class C(object):
            value = field(int, default=7)

            def __len__(self):
                return 0

        self._bind_field_name(C, 'value')

        value = C().value

        self.assertEqual(value, 7)
