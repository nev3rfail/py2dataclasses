import abc
import sys
import six
import typing

# A sentinel object to detect if a parameter is supplied or not.  Use
# a class to give it a better repr.
class _MISSING_TYPE(object):
    pass

MISSING = _MISSING_TYPE()

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
        # For InitVar, always use 'dataclasses' as the module
        if self.__class__.__name__ == 'InitVar':
            return 'dataclasses.{0}[{1}]'.format(self.__class__.__name__, type_name)
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


def _get_type_str(f_type):
    """Get a string representation of a type for docstrings."""
    if f_type is None or f_type is MISSING:
        return 'typing.Any'

    try:
        # Handle typing generics with subscripts
        if hasattr(f_type, '__origin__'):
            origin = f_type.__origin__
            if hasattr(f_type, '__args__'):
                args = f_type.__args__

                # Try to get the typing name from the type's representation
                type_repr = repr(f_type)
                # Check if it's from typing module - e.g. "typing.List[int]"
                if 'typing.' in type_repr and '[' in type_repr:
                    # Extract the typing name
                    parts = type_repr.split('[')
                    origin_name = parts[0].replace('typing.', '')
                else:
                    # Get origin name
                    if hasattr(origin, '__name__'):
                        origin_name = origin.__name__
                    elif hasattr(origin, '_name'):
                        origin_name = origin._name
                    else:
                        origin_name = str(origin)

                # Format args
                arg_strs = []
                for arg in args:
                    if hasattr(arg, '__name__'):
                        arg_strs.append(arg.__name__)
                    else:
                        arg_strs.append(str(arg).replace('typing.', ''))

                return '{0}[{1}]'.format(origin_name, ','.join(arg_strs))

        # Handle simple types
        if hasattr(f_type, '__module__') and hasattr(f_type, '__qualname__'):
            if f_type.__module__ in ('builtins', '__builtin__'):
                return f_type.__qualname__
            else:
                return f_type.__module__ + '.' + f_type.__qualname__
        elif hasattr(f_type, '__name__'):
            return f_type.__name__
        else:
            type_str = str(f_type)
            # Clean up typing annotations
            type_str = type_str.replace('typing.', '')
            if 'Union[' in type_str and 'NoneType' in type_str:
                # Convert Union[X, NoneType] to X|None
                type_str = type_str.replace('Union[', '')
                type_str = type_str.replace(', NoneType]', '|None')
                type_str = type_str.replace(', type(None)]', '|None')
            return type_str
    except (AttributeError, TypeError):
        pass

    return 'typing.Any'

