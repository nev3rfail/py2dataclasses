# * coding: utf-8 *
from __future__ import print_function
import os.path
import sys
path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src"))
sys.path.append(path)
import dataclasses

from dataclasses import dataclass

@dataclass
class Pew(object):
    field = dataclasses.field(str) # type: str
    field2 = "abs"
a = Pew("")
a.field = "123"

print(a)

