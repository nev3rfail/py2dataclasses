import os, sys
path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "."))
sys.path.insert(0, path)
from load_test import *


def load_tests(loader, tests, pattern):
    try:
        mod = __import__("tests.test_Dataclasses_py27.tests")
        suite = loader.loadTestsFromModule(mod.test_Dataclasses_py27.tests)#loader.loadTestsFromName("tests.test_Dataclasses_py27.tests")
    except:
        mod = __import__("test_Dataclasses_py27.tests")
        suite = loader.loadTestsFromModule(mod.tests)
    return suite


if __name__ == '__main__':
    unittest.main()
