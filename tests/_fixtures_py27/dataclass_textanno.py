#from __future__ import annotations

import dataclasses


class Foo(object):
    pass


@dataclasses.dataclass
class Bar(object):
    foo = dataclasses.field(Foo)
