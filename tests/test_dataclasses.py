"""Main dataclasses test suite - thin wrapper over _fixtures_py27_py314.

The actual tests live in _fixtures_py27_py314/__init__.py and are compatible
with both Python 2.7 and Python 3.14.
"""
from __future__ import absolute_import
import unittest


def load_tests(loader, tests, pattern):
    from . import _fixtures_py27_py314
    return loader.loadTestsFromModule(_fixtures_py27_py314)


if __name__ == '__main__':
    unittest.main()
