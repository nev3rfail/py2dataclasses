


import sys
import os
from collections import OrderedDict
import unittest2 as unittest
sys.modules["unittest"] = unittest
#import pytest
path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, path)
path = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "src"
))
sys.path.insert(0, path)
#print(sys.path)

import dataclasses as dataclasses


def patch_test(mod):
    # object.__setattr__(mod, "_real_field", mod.field)
    # object.__setattr__(mod, "field", field_adapter)
    #
    # object.__setattr__(mod, "_real_dataclass", mod.dataclass)
    # object.__setattr__(mod, "dataclass", dataclass_adapter)

    pass

def load_tests(loader, tests, pattern):
    # Import the real test module
    suite = loader.discover("tests.test_Dataclasses_py27", top_level_dir=os.getcwd())
    patch_test(sys.modules["tests.test_Dataclasses_py27"].common)
    return suite

if __name__ == '__main__':
    loader = unittest.TestLoader()
    root_suite = loader.discover("tests.test_Dataclasses_py27", top_level_dir=os.getcwd()) #loader.loadTestsFromName("tests.test_Dataclasses_py27")
    patch_test(sys.modules["tests.test_Dataclasses_py27"].common)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(root_suite)
#test_running()
#return pew