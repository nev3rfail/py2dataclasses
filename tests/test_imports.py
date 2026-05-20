from __future__ import absolute_import

import unittest


class TestPublicImports(unittest.TestCase):
    def test_top_level_py2dataclasses_module_imports(self):
        import py2dataclasses

        self.assertTrue(hasattr(py2dataclasses, 'dataclass'))

    def test_singleton_types_are_atomic(self):
        import _py2dataclasses.dataclasses as impl

        self.assertIn(type(None), impl._ATOMIC_TYPES)
        self.assertIn(type(Ellipsis), impl._ATOMIC_TYPES)
        self.assertIn(type(NotImplemented), impl._ATOMIC_TYPES)


if __name__ == '__main__':
    unittest.main()
