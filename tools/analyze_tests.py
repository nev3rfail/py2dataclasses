#!/usr/bin/env python
import re
from collections import defaultdict

def analyze_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find all test classes
    class_pattern = r'class (Test\w+)\(.*?\):'
    classes = re.findall(class_pattern, content)

    # Find all test methods
    test_pattern = r'def (test_\w+)\(self'
    tests = re.findall(test_pattern, content)

    # Find test methods per class
    class_tests = defaultdict(list)
    lines = content.split('\n')
    current_class = None

    for i, line in enumerate(lines):
        class_match = re.match(r'class (Test\w+)\(', line)
        if class_match:
            current_class = class_match.group(1)

        test_match = re.match(r'\s+def (test_\w+)\(self', line)
        if test_match and current_class:
            class_tests[current_class].append(test_match.group(1))

    return {
        'total_lines': len(lines),
        'classes': classes,
        'tests': tests,
        'class_tests': dict(class_tests)
    }

# Analyze both files
orig_file = 'F:/fun/py2playground/py2dataclasses/tests/__init__.orig.py'
curr_file = 'F:/fun/py2playground/py2dataclasses/tests/__init__.py'

print("Analyzing original file...")
orig = analyze_file(orig_file)

print("Analyzing current file...")
curr = analyze_file(curr_file)

print("\n" + "="*80)
print("DETAILED TEST INVENTORY ANALYSIS")
print("="*80)

print("\nORIGINAL FILE STATISTICS:")
print(f"  Total lines: {orig['total_lines']}")
print(f"  Total test methods: {len(orig['tests'])}")
print(f"  Test classes: {len(orig['classes'])}")

print("\nCURRENT FILE STATISTICS:")
print(f"  Total lines: {curr['total_lines']}")
print(f"  Total test methods: {len(curr['tests'])}")
print(f"  Test classes: {len(curr['classes'])}")

missing_tests = set(orig['tests']) - set(curr['tests'])
print("\nPROGRESS:")
print(f"  Completed: {len(curr['tests'])}")
print(f"  Total needed: {len(orig['tests'])}")
print(f"  Missing: {len(missing_tests)}")
print(f"  Progress: {len(curr['tests'])}/{len(orig['tests'])} ({100*len(curr['tests'])//len(orig['tests'])}%)")

print("\n" + "="*80)
print("ORIGINAL FILE TEST CLASSES:")
print("="*80)
for class_name in sorted(orig['class_tests'].keys()):
    tests = orig['class_tests'][class_name]
    print(f"\n{class_name}: {len(tests)} tests")
    for test in sorted(tests):
        print(f"  - {test}")

print("\n" + "="*80)
print("CURRENT FILE TEST CLASSES:")
print("="*80)
for class_name in sorted(curr['class_tests'].keys()):
    tests = curr['class_tests'][class_name]
    print(f"\n{class_name}: {len(tests)} tests")
    for test in sorted(tests):
        print(f"  - {test}")

print("\n" + "="*80)
print("MISSING TESTS BY CLASS:")
print("="*80)
for class_name in sorted(orig['class_tests'].keys()):
    orig_tests = set(orig['class_tests'].get(class_name, []))
    curr_tests = set(curr['class_tests'].get(class_name, []))
    missing = orig_tests - curr_tests

    if missing:
        print(f"\n{class_name}: {len(missing)} missing tests")
        for test in sorted(missing):
            print(f"  - {test}")

print("\n" + "="*80)
print("IMPLEMENTATION PLAN:")
print("="*80)
print(f"\nTotal missing tests to implement: {len(missing_tests)}")
print("\nMissing test methods (all classes):")
for test in sorted(missing_tests):
    print(f"  - {test}")

