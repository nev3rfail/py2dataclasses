from __future__ import absolute_import

import six
import sys
if six.PY2:
    import unittest2 as unittest
    sys.modules["unittest"] = unittest
else:
    import unittest

STANDARD = "native"
BACKPORTED = "ported"

def parse_testname(name):
    if name == STANDARD:
        return "tests._fixtures_py314"
    elif name == BACKPORTED:
        return "tests._fixtures_py27"
    else:
        return name


def get_patchers(runtime, lib, tests):
    name = parse_testname(tests)
    print(name, runtime, lib, tests)
    if runtime == "py3" and lib == STANDARD and tests == STANDARD:
        from . import _fixtures_compat_stdlib_to_backport
        patch_sys, patch_mod = _fixtures_compat_stdlib_to_backport.patch_sys,_fixtures_compat_stdlib_to_backport.patch_module,
    elif runtime == "py3" and lib == STANDARD and tests == BACKPORTED:
        from . import _fixtures_compat_stdlib_to_backport
        patch_sys, patch_mod = _fixtures_compat_stdlib_to_backport.patch_sys,_fixtures_compat_stdlib_to_backport.patch_module,
    elif runtime == "py3" and lib == BACKPORTED and tests == STANDARD:
        from . import _fixtures_compat_stdlib_to_backport
        patch_sys, patch_mod = _fixtures_compat_stdlib_to_backport.patch_sys,_fixtures_compat_stdlib_to_backport.patch_module,
    elif runtime == "py3" and lib == BACKPORTED and tests == BACKPORTED:
        from . import _fixtures_compat_stdlib_to_backport
        patch_sys, patch_mod = _fixtures_compat_stdlib_to_backport.patch_sys,_fixtures_compat_stdlib_to_backport.patch_module,
    elif (runtime == "py2" and lib == BACKPORTED and tests == BACKPORTED or (runtime == "py2" and lib == STANDARD and tests == BACKPORTED)):
        from . import _fixtures_compat_backport_to_stdlib
        patch_sys, patch_mod = lambda: None, lambda mod: mod#_fixtures_compat_backport_to_stdlib.patch_sys,_fixtures_compat_backport_to_stdlib.patch_module,
    else:
        if lib == BACKPORTED:
            from . import _fixtures_compat_stdlib_to_backport
            patch_sys, patch_mod = _fixtures_compat_stdlib_to_backport.patch_sys,_fixtures_compat_stdlib_to_backport.patch_module,
        elif name != tests:
            raise Exception("a", runtime, lib, tests)
    return (patch_mod, patch_sys)

def make_load_tests(runtime, lib, test, load):
    def load_tests(loader, tests, pattern):
        patch_mod, patch_sys = get_patchers(runtime, lib, test)
        mod = patch_module(patch_mod, patch_sys, load)
        return loader.loadTestsFromModule(mod)

    return load_tests

def patch_module(patch_mod, patch_sys, load, *args, **kwargs):
    patch_sys()
    mod = load()
    patch_mod(mod)
    return mod




