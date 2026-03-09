- This directory is a test dir for the backport of Python 3 dataclasses to python 2.7.
> The backport of tests is "human-driven AI port" meaning tests were translated from py3 to py2 by neural networks, and then were fixed by human.
- _fixtures_py314 dir contains native python 3.14 tests for the `dataclasses` lib
- _fixtures_py27 dir contains tests ported from python 3.14 to python 2.7 as closely as possible
- test_native_on_nativelib.py -- runs native python 3.14 tests on stdlib `dataclasses`
- test_native_on_portedlib.py -- runs native python 3.14 tests on backported `dataclasses` (py2dataclasses)
- test_ported_on_nativelib.py -- runs ported to py2.7 tests on stdlib `dataclasses`
- test_ported_on_portedlib.py -- runs ported to py2.7 tests on backported `dataclasses`
- test_analyzer.py -- lib to compare py314 tests to py27 tests. Ideally, they should be identical.

# Instructions
1. Do NOT create empty markdown files with descriptions of what you've done.
2. After each iteration on the codebase, append your step to THIS file.
3. Our task is to port tests from python 314 to python 2.7:
   - We have `dataclasses` module that is compatible with the mainline dataclasses module. We have shims for typing. We have shims for annotationlib. No test is unportable, if you don't know how exactly port test from py 3.14 to py 2.7 then just port it line by line, replacing f-strings with py2-compat strings and replace py3 type annotations with `field`-ones.

You need to make sure that tests ported to py2.7 represent ones from py314. Compare each test line by line. If something is missing, write the missing 2.7 test. Do not touch 314 tests, they are immutable.
your environment is powershell, your python interpreters are .\venv-py3\Scripts\python.exe and .\venv-py27\Scripts\python.exe

# The agent log goes here:
- ...