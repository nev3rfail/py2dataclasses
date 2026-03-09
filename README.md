# py2dataclasses

This repo is a PEP-557 compatible dataclass implementation for Python 2.7.

***

### Disclaimer

Sometimes systems have a proprietary legacy that is not possible
to port to newer versions of languages. But people
still need to work, systems using python 2 still have to be supported and extended.

## ⚠ WARNING

* Please, DO NOT use Python 2.7 in 2026

## Usage

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
## Development

- This is quite a straightforward convertion of dataclasses into a py2 syntax/standard done initially by neural network,
  and after that it was reviewed, fixed and finished by human.
- Tests are taken from the cpython 3.14 branch and converted to py2

## Testing

- This project aims to pass all the tests from Python 3.14
- It also aims to pass all backported tests.
