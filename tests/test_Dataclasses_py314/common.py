# Deliberately use "from dataclasses import *".  Every name in __all__
# is tested, so they all must be present.  This is a way to catch
# missing ones.

import sys
import os

import abc
import annotationlib
import io
import pickle
import inspect
import builtins
import types
import weakref
import traceback
import sys
import textwrap
import unittest
from unittest.mock import Mock
from typing import * #ClassVar, Any, List, Union, Tuple, Dict, Generic, TypeVar, Optional, Protocol, DefaultDict
import typing
from collections import deque, OrderedDict, namedtuple, defaultdict
from copy import deepcopy
from functools import total_ordering, wraps

import typing       # Needed for the string "typing.ClassVar[int]" to work as an annotation.
import dataclasses
from dataclasses import *

from test import support
from test.support import import_helper

# Just any custom exception we can catch.
class CustomError(Exception): pass

