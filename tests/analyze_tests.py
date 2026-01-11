#!/usr/bin/env python
#import six
#six.add_move(six.MovedAttribute("collections_abc", "collections", "collections.abc", "MutableMapping"))
import sys
import os

sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))

try:
    from collections import MutableMapping
except:
    # python 2 hack
    import collections
    from collections.abc import MutableMapping
    object.__setattr__(collections, "MutableMapping", MutableMapping)



def iter_tests(suite):
    """Recursively yield individual test cases from a TestSuite."""
    for item in suite:
        if isinstance(item, (unittest.TestSuite,unittest2.TestSuite,)):
            yield from iter_tests(item)
        else:
            yield item

import unittest
import unittest2
from collections import defaultdict

def analyze_tests(module_name):
    loader = unittest.TestLoader()
    root_suite = loader.loadTestsFromName(module_name)

    seen = set()
    by_class = defaultdict(list)
    standalone = []

    def walk(suite):
        for item in suite:
            if isinstance(item, (unittest.TestSuite, unittest2.TestSuite)):
                walk(item)
            else:
                # item is a TestCase or FunctionTestCase
                if isinstance(item, (unittest.FunctionTestCase, unittest2.FunctionTestCase)):
                    standalone.append(item)
                else:
                    if isinstance(item, (unittest2.loader._FailedTest, unittest.loader._FailedTest)):
                        item.debug()
                    if item not in seen:
                        seen.add(item)
                        cls = item.__class__
                        by_class[cls].append(item)

    walk(root_suite)
    return by_class, standalone

def render_test_dir(tests_dict):
    #by_class, standalone = analyze_tests(tests_dir) ## os.path.abspath(tests_dir)
    total = 0

    print("Test classes and their tests:\n")
    for container, tests in tests_dict.items():
        print(container)
        for t in tests:
            print(f"  - {t}")
        print(f"  ({len(tests)} tests)\n")
        total += len(tests)

    print(f"Total number of tests: {total}")

def diff_lists(list1, list2):
    set1 = set(list1)
    set2 = set(list2)
    return set1-set2, set2-set1

def diff_dicts(dict1, dict2, name_filter):
    ret = {}
    for key in dict1:
        dict1_name = name_filter(key)
        #if dict1_name not in dict2:
        ##    pass
        for key2 in dict2:
            dict2_name = name_filter(key2)
            if dict1_name == dict2_name:
                ret[dict1_name] = diff_lists(dict2[key2], dict1[key])
    return ret
def get_tests_data(module_name):
    by_class, standalone = analyze_tests(module_name) ## os.path.abspath(tests_dir)
    total = 0
    ret = {}
    #print("Test classes and their tests:\n")
    for cls, tests in sorted(by_class.items(), key=lambda x: x[0].__name__):
        _name = f"{cls.__module__}.{cls.__name__}"
        if _name not in ret:
            ret[_name] = []
        _t = [t._testMethodName for t in tests]
        ret[_name].extend(_t)
        total +=len(_t)

    if standalone:
        if module_name not in ret:
            ret[module_name] = []
        for t in standalone:
            ret[module_name].append(t)
            total +=1
    return total, ret

if __name__ == "__main__":
    #tests_dir = os.path.abspath("tests/py27")  # path to your tests dir

    total314, data314 = get_tests_data("test_Dataclasses_py314")

    sys.modules["unittest"] = sys.modules["unittest2"]

    total, data = get_tests_data("test_Dataclasses_py27")

    render_test_dir(data)

    print("========================")
    render_test_dir(data314)
    print("total", total)
    print("total314", total314)
    f = diff_dicts(data, data314, lambda x: x.replace("_py27", "").replace("_py314", ""))
    render_test_dir(f)
    pass


