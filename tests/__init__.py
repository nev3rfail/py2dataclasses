# # tests package init: set up sys.path for py2dataclasses
# from __future__ import print_function, absolute_import
# import os
# import sys
#
# path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
# sys.path.insert(0, path)
#
# # On Python 3, stdlib dataclasses may already be cached; flush it so our version loads
# if sys.version_info >= (3,):
#     for _k in list(sys.modules.keys()):
#         if _k == 'dataclasses' or _k.startswith('dataclasses.'):
#             del sys.modules[_k]
