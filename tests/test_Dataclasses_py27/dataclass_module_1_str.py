#from __future__ import annotations
USING_STRINGS = True

# dataclass_module_1.py and dataclass_module_1_str.py are identical
# except only the latter uses string annotations.

import dataclasses
import typing

T_CV2 = typing.ClassVar[int]
T_CV3 = typing.ClassVar

T_IV2 = dataclasses.InitVar[int]
T_IV3 = dataclasses.InitVar

@dataclasses.dataclass
class CV(object):
    T_CV4 = typing.ClassVar
    cv0 = dataclasses.field(typing.ClassVar[int], 20)
    cv1 = dataclasses.field(typing.ClassVar, 30)
    cv2 = T_CV2
    cv3 = T_CV3
    not_cv4 = dataclasses.field('T_CV4')  # string type -> not recognized as ClassVar

@dataclasses.dataclass
class IV(object):
    T_IV4 = dataclasses.InitVar
    iv0 = dataclasses.field(dataclasses.InitVar[int])
    iv1 = dataclasses.field(dataclasses.InitVar)
    iv2 = dataclasses.field(T_IV2)
    iv3 = dataclasses.field(T_IV3)
    not_iv4 = dataclasses.field('T_IV4')  # string type -> not recognized as InitVar
