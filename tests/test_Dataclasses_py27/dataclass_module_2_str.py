
USING_STRINGS = True

# dataclass_module_2.py and dataclass_module_2_str.py are identical
# except only the latter uses string annotations.

from dataclasses import dataclass, InitVar, field
from typing import ClassVar

T_CV2 = ClassVar[int]
T_CV3 = ClassVar

T_IV2 = InitVar[int]
T_IV3 = InitVar

@dataclass
class CV(object):
    T_CV4 = ClassVar
    cv0 = field(ClassVar[int], 20)
    cv1 = field(ClassVar, 30)
    cv2 = T_CV2
    cv3 = T_CV3
    not_cv4 = field('T_CV4')  # string type → not recognized as ClassVar

@dataclass
class IV(object):
    T_IV4 = InitVar
    iv0 = field(InitVar[int])
    iv1 = field(InitVar)
    iv2 = field(T_IV2)
    iv3 = field(T_IV3)
    not_iv4 = field('T_IV4')  # string type → not recognized as InitVar
