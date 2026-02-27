# py2dataclasses — Python 2.7 Usage Guide

A PEP-557 compatible `dataclasses` implementation that works on Python 2.7.

## Installation

Add the `src/` directory to your Python path and import:

```python
import sys
sys.path.insert(0, "/path/to/py2dataclasses/src")

from dataclasses import dataclass, field, fields, asdict, astuple, replace, make_dataclass, is_dataclass
from dataclasses import InitVar, ClassVar, KW_ONLY, MISSING, FrozenInstanceError
```

## Quick Start

On Python 2.7 there is no annotation syntax (`x: int`), so fields are declared using `field()` descriptors:

```python
from dataclasses import dataclass, field

@dataclass
class Point(object):
    x = field(int)
    y = field(int)

p = Point(3, 4)
print(p)        # Point(x=3, y=4)
print(p.x)      # 3
print(p == Point(3, 4))  # True
```

## Defining Fields

### Type as first argument

```python
@dataclass
class User(object):
    name = field(str)
    age = field(int)

u = User("Alice", 30)
```

### Default values

Pass a plain value as the first argument — the type is inferred automatically:

```python
@dataclass
class Config(object):
    timeout = field(30)       # default=30, type=int
    enabled = field(True)     # default=True, type=bool
    name = field("default")   # default="default", type=str

c = Config()  # all defaults
```

Or use explicit `default` keyword:

```python
@dataclass
class Config(object):
    timeout = field(int, default=30)
    name = field(str, default="default")
```

### Mutable defaults with `default_factory`

```python
@dataclass
class Container(object):
    items = field(list, default_factory=list)
    counts = field(dict, default_factory=dict)

c1 = Container()
c2 = Container()
c1.items.append(1)
assert c2.items == []  # separate instances
```

### Field options

```python
@dataclass
class Record(object):
    id = field(int)
    name = field(str)
    password = field(str, repr=False)            # hidden from repr
    timestamp = field(int, compare=False)         # excluded from == and ordering
    cached = field(str, init=False, default="")   # not in __init__
    tag = field(str, hash=False, default="")      # excluded from __hash__
```

### Metadata

```python
@dataclass
class Column(object):
    name = field(str)
    db_column = field(str, metadata={"db": True, "index": True})

f = fields(Column)[1]
print(f.metadata["db"])  # True
```

## Decorator Options

### `frozen=True` — immutable instances

```python
@dataclass(frozen=True)
class Point(object):
    x = field(float)
    y = field(float)

p = Point(1.0, 2.0)
p.x = 3.0  # raises FrozenInstanceError
```

### `order=True` — comparison operators

```python
@dataclass(order=True)
class Version(object):
    major = field(int)
    minor = field(int)
    patch = field(int)

assert Version(1, 2, 0) < Version(1, 2, 1)
assert Version(2, 0, 0) > Version(1, 9, 9)
```

### `eq=True` (default) — equality

```python
@dataclass
class Point(object):
    x = field(int)
    y = field(int)

assert Point(1, 2) == Point(1, 2)
assert Point(1, 2) != Point(3, 4)
```

### `slots=True` — memory-efficient `__slots__`

```python
@dataclass(slots=True)
class Coord(object):
    x = field(float)
    y = field(float)
    z = field(float)

c = Coord(1, 2, 3)
c.w = 4  # raises AttributeError — no __dict__
```

### `unsafe_hash=True` — force `__hash__`

```python
@dataclass(unsafe_hash=True)
class Key(object):
    x = field(int)
    y = field(int)

d = {Key(1, 2): "value"}
```

### `repr=False`, `init=False`

```python
@dataclass(repr=False)
class Secret(object):
    value = field(str)

@dataclass(init=False)
class Manual(object):
    x = field(int)
    def __init__(self):
        self.x = 42
```

## ClassVar — Class Variables

`ClassVar` fields are shared across all instances and are not included in `__init__`, `__repr__`, or comparisons:

```python
from typing import ClassVar
from dataclasses import dataclass, field

@dataclass
class Counter(object):
    count = field(ClassVar[int], 0)   # class variable with default 0
    name = field(str)

Counter.count = 10
c = Counter("test")
assert Counter.count == 10
assert len(fields(Counter)) == 1  # only 'name'
```

## InitVar — Init-Only Variables

`InitVar` fields are passed to `__init__` and `__post_init__` but are NOT stored on the instance:

```python
from dataclasses import dataclass, field, InitVar

@dataclass
class Rectangle(object):
    width = field(float)
    height = field(float)
    scale = field(InitVar[float], default=1.0)

    def __post_init__(self, scale):
        self.width *= scale
        self.height *= scale

r = Rectangle(10, 20, scale=2.0)
assert r.width == 20.0
assert r.height == 40.0
assert not hasattr(r, 'scale')  # not stored
```

## `__post_init__`

Called after `__init__`. Receives `InitVar` values as arguments:

```python
@dataclass
class C(object):
    x = field(int)
    y = field(int, init=False)

    def __post_init__(self):
        self.y = self.x * 2

c = C(5)
assert c.y == 10
```

## Keyword-Only Fields

### Per-field `kw_only`

```python
@dataclass
class Request(object):
    method = field(str)
    path = field(str)
    timeout = field(int, kw_only=True, default=30)

r = Request("GET", "/api", timeout=60)
# Request("GET", "/api", 60) would fail — timeout is keyword-only
```

### Class-level `kw_only`

```python
@dataclass(kw_only=True)
class Config(object):
    host = field(str)
    port = field(int)
    debug = field(bool, default=False)

cfg = Config(host="localhost", port=8080)
```

> **Note:** On Python 2.7, keyword-only is emulated via `**kwargs` extraction since Python 2 has no `*` separator syntax.

## Helper Functions

### `fields(class_or_instance)`

```python
from dataclasses import fields

@dataclass
class Point(object):
    x = field(int)
    y = field(int)

for f in fields(Point):
    print(f.name, f.type)
# x <class 'int'>
# y <class 'int'>
```

### `asdict(instance)`

Recursively converts to a dictionary:

```python
from dataclasses import asdict

@dataclass
class Address(object):
    street = field(str)
    city = field(str)

@dataclass
class Person(object):
    name = field(str)
    address = field(Address)

p = Person("Alice", Address("Main St", "Anytown"))
d = asdict(p)
# {'name': 'Alice', 'address': {'street': 'Main St', 'city': 'Anytown'}}
```

### `astuple(instance)`

Recursively converts to a tuple:

```python
from dataclasses import astuple

p = Point(1, 2)
assert astuple(p) == (1, 2)
```

### `replace(instance, **changes)`

Creates a copy with some fields changed:

```python
from dataclasses import replace

@dataclass(frozen=True)
class Point(object):
    x = field(int)
    y = field(int)

p1 = Point(1, 2)
p2 = replace(p1, x=10)
assert p2 == Point(10, 2)
assert p1 == Point(1, 2)  # original unchanged
```

### `make_dataclass(name, fields, ...)`

Dynamically create a dataclass:

```python
from dataclasses import make_dataclass

# Simple — just field names
Point = make_dataclass('Point', ['x', 'y'])

# With types
Point = make_dataclass('Point', [('x', int), ('y', int)])

# With defaults
Person = make_dataclass('Person', [
    ('name', str),
    ('age', int),
    ('email', str, field(str, default='unknown')),
])

p = Person("Alice", 30)
assert p.email == "unknown"
```

With base classes and custom methods:

```python
class Mixin(object):
    pass

def greet(self):
    return "Hello, " + self.name

Greeter = make_dataclass('Greeter',
    [('name', str)],
    bases=(Mixin,),
    namespace={'greet': greet})

g = Greeter("World")
assert g.greet() == "Hello, World"
```

### `is_dataclass(obj)`

```python
from dataclasses import is_dataclass

@dataclass
class C(object):
    x = field(int)

assert is_dataclass(C) == True
assert is_dataclass(C(1)) == True
assert is_dataclass(int) == False
```

## Inheritance

```python
@dataclass
class Base(object):
    x = field(int)
    y = field(int, default=0)

@dataclass
class Derived(Base):
    z = field(str, default="hello")

d = Derived(10)
assert d.x == 10
assert d.y == 0
assert d.z == "hello"
```

## Pickling

```python
import pickle

@dataclass(frozen=True)
class Data(object):
    x = field(int)
    y = field(str)

d = Data(42, "test")
restored = pickle.loads(pickle.dumps(d))
assert restored == d
```

## Combining frozen + slots

```python
@dataclass(frozen=True, slots=True)
class Vector(object):
    x = field(float)
    y = field(float)
    z = field(float)

v = Vector(1.0, 2.0, 3.0)
# v.x = 0  # FrozenInstanceError
# v.w = 0  # AttributeError
```

## Serialization / Deserialization

### `load(cls, data)` — dict to dataclass

```python
from dataclasses import dataclass, field, load

@dataclass
class User(object):
    name = field(str)
    age = field(int)

user = load(User, {"name": "Alice", "age": 30})
assert user == User("Alice", 30)
```

Nested dataclasses are handled recursively:

```python
@dataclass
class Address(object):
    city = field(str)

@dataclass
class Person(object):
    name = field(str)
    address = field(Address)

p = load(Person, {"name": "Bob", "address": {"city": "NYC"}})
assert p.address.city == "NYC"
```

Strict mode rejects extra keys:

```python
load(User, {"name": "Alice", "age": 30, "extra": 1}, strict=True)
# raises TypeError: Unknown fields for User: extra
```

### `loads(cls, json_string)` — JSON string to dataclass

```python
from dataclasses import loads

user = loads(User, '{"name": "Alice", "age": 30}')
assert user.name == "Alice"
```

### `dump(instance)` — dataclass to dict

```python
from dataclasses import dump

user = User("Alice", 30)
d = dump(user)
assert d == {"name": "Alice", "age": 30}
```

### `dumps(instance)` — dataclass to JSON string

```python
from dataclasses import dumps

s = dumps(User("Alice", 30))
# '{"name": "Alice", "age": 30}'
```

### `validate(cls, data)` / `validates(cls, json_string)` — validation without instantiation

```python
from dataclasses import validate, validates

validate(User, {"name": "Alice", "age": 30})  # returns True

validate(User, {"name": "Alice", "age": "bad"})
# raises TypeError: Field 'age' expected int, got str (value: 'bad')

validate(User, {"name": "Alice"})
# raises ValueError: Missing required field 'age' for User

validates(User, '{"name": "Alice", "age": 30}')  # returns True
```

## Python 2.7 Limitations

These Python 3 features are **not available** on Python 2.7:

| Feature | Reason |
|---------|--------|
| Annotation syntax (`x: int = 0`) | Not valid Python 2 syntax |
| Cross-type comparison TypeError | Python 2 compares any objects by type name |
| `types.GenericAlias` | Does not exist in Python 2 |
| Property shadowing InitVar | Property descriptor overwrites Field on Python 2 |

## Full Example

```python
from __future__ import print_function
from dataclasses import (dataclass, field, fields, asdict, astuple,
                         replace, make_dataclass, is_dataclass, InitVar,
                         load, loads, dump, dumps, validate, validates)
from typing import ClassVar

@dataclass
class Address(object):
    street = field(str)
    city = field(str)
    zipcode = field(str, default="00000")

@dataclass
class Person(object):
    company = field(ClassVar[str], "Acme Corp")
    name = field(str)
    age = field(int)
    address = field(Address)
    salary_multiplier = field(InitVar[float], default=1.0)
    salary = field(int, default=50000)

    def __post_init__(self, salary_multiplier):
        self.salary = int(self.salary * salary_multiplier)

addr = Address("123 Main St", "Anytown")
person = Person("Alice", 30, addr, salary_multiplier=1.5)

print(person)
# Person(name='Alice', age=30, address=Address(...), salary=75000)

print(asdict(person))
# {'name': 'Alice', 'age': 30, 'address': {...}, 'salary': 75000}

person2 = replace(person, age=31)
assert person2.age == 31
assert person.age == 30

assert Person.company == "Acme Corp"
assert is_dataclass(person)
```
