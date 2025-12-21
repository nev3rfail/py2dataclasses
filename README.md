# py2dataclasses

This repo is a somewhat PEP-557 compatible dataclass implementation for Python 2.7.

***

### Disclaimer

Sometimes systems have a proprietary legacy that is not possible
to port to newer versions of languages. But people
still need to work, systems using python 2 still have to be supported and extended.

## ⚠ WARNING

* DO NOT use python 2.7 in 2026
* Really, DO NOT use py2 in 2026
* [Please, read Python 3 migration statement](https://python3statement.github.io/)

## Safety

> ⚠ Hazmat

- Many things are missing
- Even more things are present but working improperly

## Development

- This is quite a straightforward convertion of dataclasses into a py2 syntax/standard done initially by neural network,
  and after that it was reviewed, fixed and finished by human.
- Tests are stolen from cpython 3.14 branch and converted (poorly) to py2
- This is **not** production ready (yet)
- Contributions are welcome ~~please help~~

## Testing

- All tests are broken drafts for now
