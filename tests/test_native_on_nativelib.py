# -*- coding: utf-8 -*-
from tests._fixtures_loader import make_load_tests
import six

def import_fixture():
    from . import _fixtures_py314
    return _fixtures_py314


load_tests = make_load_tests("py2" if six.PY2 else "py3", "native", "native", load=import_fixture)