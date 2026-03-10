import sys

import xml.etree.ElementTree as ET
import json


def classify_testcase(case):
    if case.find('failure') is not None:
        return 'failure'
    if case.find('error') is not None:
        return 'error'
    if case.find('skipped') is not None:
        return 'skipped'
    return 'passed'

def get_field_caption(classified):
    if classified == 'failure':
        return 'failures'
    if classified == 'error':
        return 'errors'
    if classified == 'skipped':
        return 'skipped'
    return 'passed'


def junit_summary(xml_string):
    root = ET.fromstring(xml_string)

    global_counts = {
        "tests": 0,
        "passed": 0,
        "failures": 0,
        "errors": 0,
        "skipped": 0
    }

    suites = []

    for suite in root.iter('testsuite'):
        suite_counts = {
            "name": suite.attrib.get("name"),
            "tests": 0,
            "passed": 0,
            "failures": 0,
            "errors": 0,
            "skipped": 0
        }

        for case in suite.findall('testcase'):
            status = classify_testcase(case)

            suite_counts["tests"] += 1
            suite_counts[get_field_caption(status)] += 1

            global_counts["tests"] += 1
            global_counts[get_field_caption(status)] += 1

        suites.append(suite_counts)

    return {
        "summary": global_counts,
        "testsuites": suites
    }


if __name__ == "__main__":
    data = junit_summary(sys.stdin.read())
    print(json.dumps(data, indent=4))