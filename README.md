# py2dataclasses

This project is a PEP-557 compatible dataclass implementation for Python 2.7.

## Usage

1. `pip install py2dataclasses`
2. ```python
    # We have to use `field` syntax because Python 2 doesn't support type annotations.
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

<details>
<summary>Big fat (working!) example</summary>

```python
from __future__ import print_function
from dataclasses import (dataclass, field, fields, asdict, astuple,
                         replace, make_dataclass, is_dataclass, InitVar,)
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
</details>

More examples [here](PYTHON2_USAGE.md).


## Development


#### Several testenvs provided to run tests in different configurations:

- ![test_ported_on_portedlib_py27](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Fnev3rfail%2F73107a0cfbdf6977a5b43352761da183%2Fraw%2Feb97723d48f5073d69660cf11134d55bbf944eb2%2Fbadge.test_ported_on_portedlib_py27.json)
  - >runs ported to py2.7 tests on backported `dataclasses` (runs with py27)
- ![test_ported_on_portedlib](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Fnev3rfail%2F73107a0cfbdf6977a5b43352761da183%2Fraw%2Feb97723d48f5073d69660cf11134d55bbf944eb2%2Fbadge.test_ported_on_portedlib.json)
  - >runs ported to py2.7 tests on backported `dataclasses` (runs with py3)
- ![test_native_on_nativelib](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Fnev3rfail%2F73107a0cfbdf6977a5b43352761da183%2Fraw%2Feb97723d48f5073d69660cf11134d55bbf944eb2%2Fbadge.test_native_on_nativelib.json)
  - >runs native python 3.14 tests on stdlib `dataclasses` (runs with py3)
- ![test_native_on_portedlib](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Fnev3rfail%2F73107a0cfbdf6977a5b43352761da183%2Fraw%2Feb97723d48f5073d69660cf11134d55bbf944eb2%2Fbadge.test_native_on_portedlib.json)
  - >runs native python 3.14 tests on backported `dataclasses` (runs with py3)
- ![test_ported_on_nativelib](https://img.shields.io/endpoint?url=https%3A%2F%2Fgist.githubusercontent.com%2Fnev3rfail%2F73107a0cfbdf6977a5b43352761da183%2Fraw%2Feb97723d48f5073d69660cf11134d55bbf944eb2%2Fbadge.test_ported_on_nativelib.json)
  - >runs ported to py2.7 tests on stdlib `dataclasses` (runs with py3)

#### Fixtures
- `tests._fixtures_py314` dir contains original python 3.14 tests for the `dataclasses` lib. Test themselves are in `__init__.py`
- `tests._fixtures_py27` dir contains tests ported from python 3.14 to python 2.7 as closely as possible. Test themselves are in `__init__.py`

#### Helpers
- `tests._xmlrunner` is a helper to run coverage alongside tests
- `tests._xmlprocessor` is a helper for the CI

#### Adapters
- `tests._fixtures_compat_backport_to_stdlib`
- `tests._fixtures_compat_stdlib_to_backport`

#### Source
- `dataclasses`
- `_py2dataclasses`

### ⚠ WARNING
* Please, do not use Python 2.7 in 2026


