import os.path

from xmlrunner.runner import XMLTestProgram, XMLTestRunner
from xmlrunner.result import _XMLTestResult as original_XMLTestResult

# ultra crutch for parser:
# _report_testsuite puts a nonexistent file in the xml, and breaks codecov
_orig_report_testsuite = original_XMLTestResult._report_testsuite

def _report_testsuite(suite_name, tests, xml_document, parentElement,
                      properties):
    suite = _orig_report_testsuite(suite_name, tests, xml_document, parentElement,
                                                     properties)
    file = suite.getAttribute("file")
    if file and not os.path.exists(file):
        module_name = suite_name.rpartition('.')[0]
        qual = module_name.replace('.', '/')
        if os.path.exists(qual):
            n = qual + "/__init__.py"
            if os.path.exists(n):
                suite.setAttribute("file", n)
    return suite

original_XMLTestResult._report_testsuite = staticmethod(_report_testsuite)


XMLTestProgram(module=None)