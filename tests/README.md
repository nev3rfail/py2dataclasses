- This directory is a test dir for the backport of Python 3 dataclasses to python 2.7.
> The backport of tests is "human-driven AI port" meaning tests were translated from py3 to py2 by neural networks, and then were fixed by human.
- _fixtures_py314 dir contains native python 3.14 tests for the `dataclasses` lib
- _fixtures_py27 dir contains tests ported from python 3.14 to python 2.7 as closely as possible
- test_native_on_nativelib.py -- runs native python 3.14 tests on stdlib `dataclasses`
- test_native_on_portedlib.py -- runs native python 3.14 tests on backported `dataclasses` (py2dataclasses)
- test_ported_on_nativelib.py -- runs ported to py2.7 tests on stdlib `dataclasses`
- test_ported_on_portedlib.py -- runs ported to py2.7 tests on backported `dataclasses`
- test_analyzer.py -- lib to compare py314 tests to py27 tests. Ideally, they should be identical.

# The log goes here: