# -*- coding: utf-8 -*-
from tests._fixtures_loader import make_load_tests
import six

def import_fixture():
    from . import _fixtures_py27
    return _fixtures_py27


load_tests = make_load_tests("py2" if six.PY2 else six.PY3, "native", "ported", load=import_fixture)