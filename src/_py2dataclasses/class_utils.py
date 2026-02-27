

def is_descriptor(obj):
    """Returns True if obj is a descriptor, False otherwise."""
    return (
            hasattr(obj, '__get__') or
            hasattr(obj, '__set__') or
            hasattr(obj, '__delete__'))

def type_qualname(o):
    klass = o.__class__
    return qualname(klass)

def qualname(o):
    existing = getattr(o, "__qualname__", None)
    if existing:
        return existing

    klass = o
    module = klass.__module__
    if module == '__builtin__':
        return klass.__name__ # avoid outputs like '__builtin__.str'
    return module + '.' + klass.__name__