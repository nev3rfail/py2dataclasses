# -*- coding: utf-8 -*-
from tests._fixtures_loader import make_load_tests
import six

def import_fixture():
    from . import _fixtures_py314
    # a stub so pickling works
    _fixtures_py314.FrozenSlotsClass = _fixtures_py314.TestSlots.FrozenSlotsClass
    _fixtures_py314.FrozenWithoutSlotsClass = _fixtures_py314.TestSlots.FrozenWithoutSlotsClass
    _fixtures_py314.FrozenSlotsGetStateClass = _fixtures_py314.TestSlots.FrozenSlotsGetStateClass
    _fixtures_py314.FrozenSlotsSetStateClass = _fixtures_py314.TestSlots.FrozenSlotsSetStateClass
    _fixtures_py314.FrozenSlotsAllStateClass = _fixtures_py314.TestSlots.FrozenSlotsAllStateClass

    return _fixtures_py314


load_tests = make_load_tests("py2" if six.PY2 else "py3", "ported", "native", load=import_fixture)