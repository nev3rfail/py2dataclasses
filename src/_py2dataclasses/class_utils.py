

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
    #return compute_qualname(o)
    existing = getattr(o, "__qualname__", None)
    if existing:
        return existing
    klass = o
    module = klass.__module__
    if module == '__builtin__':
        return klass.__name__ # avoid outputs like '__builtin__.str'
    return module + '.' + klass.__name__

import inspect

def compute_qualname(cls):
    if hasattr(cls, "__qualname__"):
        return cls.__qualname__

    name = cls.__name__

    frame = inspect.currentframe()
    try:
        frame = frame.f_back
        parts = []

        while frame:
            code_name = frame.f_code.co_name
            if code_name == '<module>':
                break

            if 'self' in frame.f_locals:
                parts.append(frame.f_locals['self'].__class__.__name__)

            parts.append(code_name)
            parts.append('<locals>')
            frame = frame.f_back

        parts.reverse()
        parts.append(name)
        return ".".join(parts)
    finally:
        del frame