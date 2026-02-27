import abc
import sys
import six
import typing


class _GenericMeta(abc.ABCMeta):
    def __getitem__(cls, typ):
        #n = type("{}[{}]".format(cls.__name__, typ.__name__), (cls,), {"__origin__":weakref.ref(cls), "__parameters__":typ})
        #n.__module__ = cls.__module__
        return cls(typ)

@six.add_metaclass(_GenericMeta)
class GenericAlias(object):
    #__metaclass__ = _GenericMeta
    __slots__ = ('type',)
    def __init__(self, type_):
        self.type = type_
    # def __new__(cls, type_):
    #     #cls.__init__
    #     cls.type = type_
    #pass
    def __repr__(self):
        if isinstance(self.type, type):
            try:
                type_name = self.type.__name__
            except:
                type_name = repr(self.type)
        else:
            # typing objects, e.g. List[int]
            type_name = repr(self.type)
        return '{0}.{1}[{2}]'.format(self.__class__.__module__, self.__class__.__name__, type_name)
#f = typing.GenericMeta

def make_alias(name, * _types, **kwargs):
    if "module" in kwargs:
        module = kwargs["module"]
    else:
        module = sys._getframe(1).f_globals.get('__name__', '__main__')
    #t = type("{}[{}]".format(name, ",".join(_types)), (GenericAlias,), {"__name__":name,"__args__":_types})
    t = type("{}".format(name), (GenericAlias,),{}) #, {"__name__":name,"__args__":_types})
    #if module is not None:
    t.__module__ = module
    return t


# ---------------------------------------------------------------------------
# Type introspection helpers for load/loads validation
# ---------------------------------------------------------------------------

def _get_type_origin(tp):
    """Get the origin of a generic type.
    List[int] -> list, Dict[str, int] -> dict, Optional[int] -> Union.
    Returns None for non-generic types.
    """
    return getattr(tp, '__origin__', None)


def _get_type_args(tp):
    """Get the type arguments of a generic type.
    List[int] -> (int,), Dict[str, int] -> (str, int).
    Returns () for non-generic types.
    """
    return getattr(tp, '__args__', ()) or ()


def _is_optional(tp):
    """If tp is Optional[X] (Union[X, None]), return X. Otherwise return None."""
    origin = _get_type_origin(tp)
    if origin is typing.Union:
        args = _get_type_args(tp)
        non_none = [a for a in args if a is not type(None)]
        if len(non_none) == 1 and type(None) in args:
            return non_none[0]
    return None


def _origin_is(origin, builtin_type):
    """Check if a type origin matches a builtin type, handling Py2/Py3 typing compat."""
    if origin is builtin_type:
        return True
    _mapping = {list: 'List', dict: 'Dict', tuple: 'Tuple', set: 'Set', frozenset: 'FrozenSet'}
    typing_name = _mapping.get(builtin_type)
    if typing_name:
        return origin is getattr(typing, typing_name, None)
    return False


def _resolve_type(tp, type_vars):
    """Substitute TypeVars in a type annotation using the type_vars mapping.

    Examples with type_vars={T: int}:
        T           -> int
        List[T]     -> List[int]
        Dict[str,T] -> Dict[str, int]
        Tuple[T,T]  -> Tuple[int, int]
        Optional[T] -> Optional[int]
        int         -> int (unchanged)
    """
    if not type_vars:
        return tp

    # Direct TypeVar match
    if isinstance(tp, typing.TypeVar):
        return type_vars.get(tp, tp)

    # Generic type with args -- recurse into args
    origin = _get_type_origin(tp)
    args = _get_type_args(tp)
    if origin is not None and args:
        new_args = tuple(_resolve_type(a, type_vars) for a in args)
        if new_args != args:
            # Rebuild the generic type with resolved args
            # Use origin[new_args] for typing generics
            try:
                if len(new_args) == 1:
                    return origin[new_args[0]]
                return origin[new_args]
            except TypeError:
                return tp
    return tp

