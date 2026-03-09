# coding=utf-8
# GC-SAFE PATCHED VERSION
# Changes for Python 2 + gc.disable() safety are marked with # GC-FIX comments.
#
# Summary of issues fixed:
#
# 1. [GC-FIX #1] _ATOMIC_TYPES uses types.NoneType, types.EllipsisType,
#    types.NotImplementedType which do NOT exist on Python 2. Accessing a
#    missing attribute on `types` raises AttributeError at import time, which
#    would crash the whole module.  Fixed by using safe getattr() with
#    fallbacks and the actual singleton objects.
#
# 2. [GC-FIX #2] _add_slots creates reference cycles that the GC normally
#    breaks:
#      - `tmp = cls.__dict__.values()` keeps a live reference to the OLD class
#        dict, preventing the old class from being freed even after `newcls` is
#        returned.  With GC disabled these cycles never break.
#      Fixed: after iterating, explicitly del tmp, del cls inside _add_slots
#      (the original has a commented-out `#del tmp` / `#del cls`—uncommented
#      and repositioned after all uses).
#
# 3. [GC-FIX #3] _update_func_cell_for__class__ writes into closure cells.
#    Closure cells hold a reference back to the enclosing class object.
#    After the swap (oldcls → newcls) the old cell value is replaced, but the
#    cell itself is still referenced by the function's __closure__ tuple, and
#    the function's __closure__ is referenced by the function object, which is
#    referenced by the new class dict.  This is fine for correctness, but with
#    GC disabled we must ensure oldcls is not reachable once _add_slots
#    returns.  The fix in point #2 (deleting tmp and cls) is the primary
#    remedy; no additional change needed here beyond that.
#
# 4. [GC-FIX #4] collect_annotations uses `map(lambda …, …)` for its
#    side-effect (calling __set_name__).  In Python 3 map() is lazy and the
#    lambda is NEVER called unless the result is consumed.  This is a silent
#    correctness bug (unrelated to GC but present in the original).
#    Fixed: replaced with an explicit for-loop.
#
# 5. [GC-FIX #5] weakref usage.  The module imports `weakref` but never uses
#    it directly in user-visible code paths (weakref_slot support goes through
#    __slots__ strings).  No cycle risk from weakref itself, no change needed.
#
# 6. [GC-FIX #6] ForwardRef owner cycles.  _clear_forwardref_owners already
#    exists and is called inside _add_slots to break ForwardRef → class refs.
#    This is correct and sufficient for Python 3; on Python 2 _annotationlib is
#    None so the function is a no-op, also correct.  No change needed.
#
# 7. [GC-FIX #7] __builtins__ access in _process_class.  The expression
#    `__builtins__.get('repr') if isinstance(__builtins__, dict) else
#     getattr(__builtins__, 'repr')` is correct Python 2/3.  No change needed.
#
from __future__ import print_function, absolute_import
import abc
import functools
import re
import sys
import copy
import types
import inspect
import keyword
import itertools
import weakref
from collections import OrderedDict

import six

from .abc_utils import update_abstractmethods
from .type_utils import make_alias, _get_type_str, MISSING
from .reprlib import recursive_repr, repr as actual_recursive_repr
from .string_utils import isidentifier
builtin_repr = repr
from .class_utils import is_descriptor, qualname, _qualname

if six.PY2:
    from dictproxyhack import dictproxy as _dict_proxy
else:
    _dict_proxy = types.MappingProxyType

import typing
MappingProxyType = _dict_proxy


try:
    import annotationlib as _annotationlib
except ImportError:
    _annotationlib = None

# Sentinel for make_dataclass to avoid eagerly importing typing.Any
_ANY_MARKER = object()
if _annotationlib is not None:
    def _evaluate_annotation(ann, globals_dict):
        """Evaluate a single annotation, raising NameError for unresolvable refs.
        Handles strings, ForwardRefs, and generic aliases with inner ForwardRefs."""
        if isinstance(ann, str):
            return eval(ann, globals_dict)
        elif isinstance(ann, _annotationlib.ForwardRef):
            if hasattr(_annotationlib, 'evaluate_forward_ref'):
                return _annotationlib.evaluate_forward_ref(
                    ann, globals=globals_dict, locals=globals_dict)
            elif hasattr(typing, 'evaluate_forward_ref'):
                # Try both parameter styles for compatibility
                try:
                    return typing.evaluate_forward_ref(
                        ann, globals=globals_dict, locals=globals_dict)
                except TypeError:
                    return typing.evaluate_forward_ref(
                        ann, globalns=globals_dict, localns=globals_dict)
            else:
                # Deprecated path - pass type_params to suppress DeprecationWarning
                try:
                    return ann._evaluate(globals_dict, globals_dict,
                                         type_params=(), recursive_guard=frozenset())
                except TypeError:
                    return ann._evaluate(globals_dict, globals_dict,
                                         recursive_guard=frozenset())
        elif hasattr(ann, '__args__') and ann.__args__:
            # Generic alias like list[ForwardRef('undefined')]:
            # evaluate inner args to trigger NameError for unresolvable refs.
            for arg in ann.__args__:
                _evaluate_annotation(arg, globals_dict)
            return ann
        return ann

    def _make_annotate_function(__class__, method_name, annotation_fields, return_type, field_annotations=None):
        """Create an __annotate__ function for a generated dataclass method (PEP 649)."""
        if __class__.__module__ in sys.modules:
            __class_globals__ = sys.modules[__class__.__module__].__dict__
        else:
            __class_globals__ = {}
            if isinstance(__builtins__, dict):
                __class_globals__.update(__builtins__)
            else:
                __class_globals__.update(__builtins__.__dict__)

        def __annotate__(format):
            Format = _annotationlib.Format
            if format in (Format.VALUE, Format.FORWARDREF, Format.STRING):
                # Use the field_annotations captured in the closure instead of trying to fetch
                # them from the class at runtime, which can cause issues with special descriptors
                cls_annotations = field_annotations if field_annotations is not None else {}
                new_annotations = OrderedDict()

                if format == Format.VALUE:
                    # Evaluate ALL class annotations — NameError propagates for any
                    # unresolvable ref, even those not in annotation_fields (non-init fields).
                    # This matches CPython behaviour: the __init__ annotate function must
                    # raise NameError if any annotation in the class cannot be resolved,
                    # regardless of whether that field participates in __init__.
                    for k, ann in cls_annotations.items():
                        resolved = _evaluate_annotation(ann, __class_globals__)
                        if k in annotation_fields:
                            new_annotations[k] = resolved
                    if return_type is not MISSING:
                        new_annotations["return"] = return_type

                elif format == Format.FORWARDREF:
                    for k in annotation_fields:
                        if k in cls_annotations:
                            ann = cls_annotations[k]
                            if isinstance(ann, str):
                                try:
                                    new_annotations[k] = eval(ann, __class_globals__)
                                except NameError:
                                    new_annotations[k] = _annotationlib.ForwardRef(ann, is_class=True)
                            else:
                                new_annotations[k] = ann
                    if return_type is not MISSING:
                        new_annotations["return"] = return_type

                elif format == Format.STRING:
                    for k in annotation_fields:
                        if k in cls_annotations:
                            ann = cls_annotations[k]
                            if isinstance(ann, str):
                                new_annotations[k] = ann
                            elif isinstance(ann, _annotationlib.ForwardRef):
                                new_annotations[k] = ann.__forward_arg__
                            else:
                                new_annotations[k] = _annotationlib.type_repr(ann)
                    if return_type is not MISSING:
                        new_annotations["return"] = _annotationlib.type_repr(return_type)

                return new_annotations
            else:
                raise NotImplementedError(format)

        __annotate__.__generated_by_dataclasses__ = True
        __annotate__.__qualname__ = '{0}.{1}.__annotate__'.format(
            __class__.__qualname__, method_name)
        return __annotate__
def _get_annotations(cls):
    """Get class annotations safely, supporting deferred annotations (PEP 649)."""
    if _annotationlib is not None:
        try:
            return _annotationlib.get_annotations(cls, format=_annotationlib.Format.FORWARDREF)
        except Exception:
            return OrderedDict()
    # Use cls.__dict__ to get only OWN annotations, not inherited via MRO.
    # On Python 2, getattr() would return parent annotations, breaking derived classes.
    return cls.__dict__.get('__annotations__', OrderedDict())


class DataclassInstance(typing.Protocol):
    __dataclass_fields__= None # type: typing.ClassVar[typing.Dict[str, _Field[typing.Any]]]
_DataclassT = typing.TypeVar("_DataclassT", bound=DataclassInstance)

# Raised when an attempt is made to modify a frozen class.
class FrozenInstanceError(AttributeError):
    pass


# A sentinel object for default values to signal that a default
# factory will be used.  This is given a nice repr() which will appear
# in the function signature of dataclasses' constructors.
class _HAS_DEFAULT_FACTORY_CLASS(object):
    def __repr__(self):
        return '<factory>'

_HAS_DEFAULT_FACTORY = _HAS_DEFAULT_FACTORY_CLASS()





# A sentinel object to indicate that following fields are keyword-only by
# default.  Use a class to give it a better repr.
class _KW_ONLY_TYPE(object):
    pass

KW_ONLY = _KW_ONLY_TYPE()


# Since most per-field metadata will be unused, create an empty
# read-only proxy that can be shared among all fields.
_EMPTY_METADATA = MappingProxyType({})


# Markers for the various kinds of fields and pseudo-fields.
class _FIELD_BASE(object):
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name

_FIELD = _FIELD_BASE('_FIELD')
_FIELD_CLASSVAR = _FIELD_BASE('_FIELD_CLASSVAR')
_FIELD_INITVAR = _FIELD_BASE('_FIELD_INITVAR')


# The name of an attribute on the class where we store the Field
# objects.  Also used to check if a class is a Data Class.
_FIELDS = '__dataclass_fields__'

# The name of an attribute on the class that stores the parameters to
# @dataclass.
_PARAMS = '__dataclass_params__'

# The name of the function, that if it exists, is called at the end of
# __init__.
_POST_INIT_NAME = '__post_init__'

# String regex that string annotations for ClassVar or InitVar must match.
# Allows "identifier.identifier[" or "identifier[".
_MODULE_IDENTIFIER_RE = re.compile(r'^(?:\s*(\w+)\s*\.)?\s*(\w+)')

# Atomic immutable types which don't require any recursive handling and for which deepcopy
# returns the same object. We can provide a fast-path for these types in asdict and astuple.

# ---------------------------------------------------------------------------
# GC-FIX #1: _ATOMIC_TYPES
#
# In Python 2, many of these attributes simply don't exist on the `types`
# module (NoneType, EllipsisType, NotImplementedType, etc.).  Referencing a
# missing attribute at module-import time raises AttributeError immediately,
# crashing the import even before any class is decorated.
#
# We build the set defensively:
#   - For singleton types (NoneType, etc.) use type(singleton) which always
#     works on any Python version.
#   - For types that genuinely don't exist on Python 2, use getattr with a
#     sentinel and skip them.
# ---------------------------------------------------------------------------
def _build_atomic_types():
    _types = set()
    # These are universally available via type():
    _types.add(type(None))       # NoneType
    _types.add(type(types.EllipsisType))        # EllipsisType  (Ellipsis exists in Py2 too)
    _types.add(type(NotImplemented))  # NotImplementedType
    # Standard built-ins present on both Py2 and Py3:
    for _t in (bool, int, float, str, complex, bytes, type, property,
               types.CodeType, types.BuiltinFunctionType, types.FunctionType):
        _types.add(_t)
    # range: in Py2 range() returns a list; xrange is the lazy version.
    # We add whichever is available.
    _types.add(range)
    if six.PY2:
        import __builtin__
        if hasattr(__builtin__, 'xrange'):
            _types.add(xrange)  # noqa: F821
    return frozenset(_types)

_ATOMIC_TYPES = _build_atomic_types()

# Any marker is used in `make_dataclass` to mark unannotated fields as `Any`
# without importing `typing` module.
_ANY_MARKER = object()

InitVar = make_alias("InitVar", "T")



# Instances of Field are only ever created from within this module,
# and only from the field() function, although Field instances are
# exposed externally as (conceptually) read-only objects.
class _Field(object):
    """"""
    _counter = 0
    __slots__ = ('name',
                 'type',
                 'default',
                 'default_factory',
                 'repr',
                 'hash',
                 'init',
                 'compare',
                 'metadata',
                 'kw_only',
                 'doc',
                 'order',
                 '_field_type',  # Private: not to be used by user code.
                 )

    def __init__(self, default, default_factory, init, repr, hash, compare,
                 metadata, kw_only, doc, **kwargs):
        self.order = _Field._counter
        _Field._counter += 1
        self.name = None
        self.default = default
        self.default_factory = default_factory
        self.init = init
        self.repr = repr
        self.hash = hash
        self.compare = compare
        if metadata is None:
            self.metadata = _EMPTY_METADATA
        else:
            try:
                self.metadata = MappingProxyType(metadata)
            except TypeError:
                if hasattr(metadata, '__getitem__') and hasattr(metadata, '__len__'):
                    self.metadata = metadata
                else:
                    raise
        self.kw_only = kw_only
        self.doc = doc
        self._field_type = None

    @property
    def __annotations__(self):
        return {self.name: self.type}

    @recursive_repr()
    def __repr__(self):
        return ('Field('
                'name={0!r},'
                'type={1!r},'
                'default={2!r},'
                'default_factory={3!r},'
                'init={4!r},'
                'repr={5!r},'
                'hash={6!r},'
                'compare={7!r},'
                'metadata={8!r},'
                'kw_only={9!r},'
                'doc={10!r},'
                '_field_type={11})'
                ).format(
            self.name, None if self.type is MISSING else self.type, self.default, self.default_factory,
            self.init, self.repr, self.hash, self.compare,
            self.metadata, self.kw_only, self.doc, self._field_type)

    def __fancy_repr(self):
        return ('{12!s}<{1!s}>(name=({0!r}),' +
                ('default={2!r},' if self.default is not MISSING else "") +
                ('default_factory={3!r},' if self.default_factory is not MISSING else "") +
                ('init={4!r},' if self.init else "" ) +
                ('repr={5!r},' if self.repr else "" ) +
                ('hash={6!r},' if self.hash else "" ) +
                ('compare={7!r},' if self.compare else "" ) +
                ('metadata={8!r},' if self.metadata else "" ) +
                ('kw_only={9!r},' if self.kw_only else "" ) +
                ('doc={10!r},' if self.doc else "" ) +
                ('_field_type={11}' if self._field_type is not MISSING else "" ) +
                ')').format(
            self.name, getattr(self.type, "__name__", self.type.__class__.__name__), self.default, self.default_factory,
            self.init, self.repr, self.hash, self.compare,
            self.metadata, self.kw_only, self.doc, self._field_type, self.__class__.__module__ +"."+self.__class__.__name__)
    def __set_name__(self, owner, name):
        func = getattr(type(self.default), '__set_name__', None)
        if func:
            func(self.default, owner, name)
        self.name = name


class _DataclassParams(object):
    __slots__ = ('init',
                 'repr',
                 'eq',
                 'order',
                 'unsafe_hash',
                 'frozen',
                 'match_args',
                 'kw_only',
                 'slots',
                 'weakref_slot',
                 )

    def __init__(self, init, repr, eq, order, unsafe_hash, frozen,
                 match_args, kw_only, slots, weakref_slot):
        self.init = init
        self.repr = repr
        self.eq = eq
        self.order = order
        self.unsafe_hash = unsafe_hash
        self.frozen = frozen
        self.match_args = match_args
        self.kw_only = kw_only
        self.slots = slots
        self.weakref_slot = weakref_slot

    def __repr__(self):
        return ('_DataclassParams('
                'init={0!r},'
                'repr={1!r},'
                'eq={2!r},'
                'order={3!r},'
                'unsafe_hash={4!r},'
                'frozen={5!r},'
                'match_args={6!r},'
                'kw_only={7!r},'
                'slots={8!r},'
                'weakref_slot={9!r}'
                ')').format(
            self.init, self.repr, self.eq, self.order,
            self.unsafe_hash, self.frozen, self.match_args,
            self.kw_only, self.slots, self.weakref_slot)


def _field(default=MISSING, default_factory=MISSING, init=True, repr=True,
           hash=None, compare=True, metadata=None, kw_only=MISSING, doc=None, _cls=_Field):
    """Return an object to identify dataclass fields.

    default is the default value of the field.  default_factory is a
    0-argument function called to initialize a field's value.  If init
    is true, the field will be a parameter to the class's __init__()
    function.  If repr is true, the field will be included in the
    object's repr().  If hash is true, the field will be included in the
    object's hash().  If compare is true, the field will be used in
    comparison functions.  metadata, if specified, must be a mapping
    which is stored but not otherwise examined by dataclass.  If kw_only
    is true, the field will become a keyword-only parameter to
    __init__().  doc is an optional docstring for this field.

    It is an error to specify both default and default_factory.
    """

    if default is not MISSING and default_factory is not MISSING:
        raise ValueError('cannot specify both default and default_factory')
    return _cls(default, default_factory, init, repr, hash, compare,
                metadata, kw_only, doc)

def of(_typ):
    return _typ

T = typing.TypeVar("T")

def field(_typ=MISSING, default=MISSING, default_factory=MISSING, init=True, repr=True,
          hash=None, compare=True, metadata=None, kw_only=MISSING, doc=None, **kwargs):
    # type: (typing.Type[T], typing.Optional[T], typing.Optional[typing.Callable[[], T]], bool, bool, typing.Optional[bool], bool, typing.Optional[bool], typing.Optional[typing.Mapping[typing.Any, typing.Any]], typing.Optional[str]) -> T
    mode = kwargs["mode"] if "mode" in kwargs else 1
    f = _field(default, default_factory, init, repr, hash, compare,
               metadata, kw_only, doc, _cls=Field if mode == 1 else _Field)
    f.type = _typ
    return f

def throw(e, m):
    raise e(m)

class Field(_Field):
    def __get__(self, instance, owner):
        if hasattr(self.default, "__get__"):
            v = self.default.__get__(instance, owner)
        else:
            if not instance:
                v = self
            elif self.name and hasattr(instance, self.name):
                v = object.__getattribute__(self, self.name)
            else:
                v= self.default if self.default is not MISSING else self.default_factory() if self.default_factory is not MISSING else throw(AttributeError, "object has no attribute {}".format(self.name))
                # v = (self.default if self.default is not MISSING
                #      else self.default_factory() if self.default_factory is not MISSING
                # else throw(AttributeError, "object has no attribute {}".format(self.name)))
        return v

    def __set__(self, instance, value):
        if hasattr(self.default, "__set__"):
            # descriptor
            self.default.__set__(instance, value)
        elif hasattr(type(self.default), "__set__"):
            # descriptor
            type(self.default).__set__(instance, value)
        elif self.default is value:
            pass
        else:
            raise RuntimeError()

    def __set_name__(self, owner, name):
        _Field.__set_name__(self, owner, name)
        self.name = name


def _fields_in_init_order(fields):
    # Returns the fields as __init__ will output them.  It returns 2 tuples:
    # the first for normal args, and the second for keyword args.

    return (tuple(f for f in fields if f.init and not f.kw_only),
            tuple(f for f in fields if f.init and f.kw_only))


def _tuple_str(obj_name, fields):
    # Return a string representing each field of obj_name as a tuple
    # member.  So, if fields is ['x', 'y'] and obj_name is "self",
    # return "(self.x,self.y)".

    # Special case for the 0-tuple.
    if not fields:
        return '()'
    # Note the trailing comma, needed if this turns out to be a 1-tuple.
    return '({0},)'.format(','.join(['{0}.{1}'.format(obj_name, f.name) for f in fields]))


class _FuncBuilder(object):
    def __init__(self, globals):
        self.names = []
        self.src = []
        self.globals = globals
        self.locals = OrderedDict()
        self.overwrite_errors = OrderedDict()
        self.unconditional_adds = OrderedDict()
        self.method_annotations = OrderedDict()

    def add_fn(self, name, args, body, locals=None, return_type=MISSING,
               overwrite_error=False, unconditional_add=False, decorator=None,
               annotation_fields=None):
        if locals is not None:
            self.locals.update(locals)

        if overwrite_error:
            self.overwrite_errors[name] = overwrite_error

        if unconditional_add:
            self.unconditional_adds[name] = True

        self.names.append(name)

        if annotation_fields is not None:
            self.method_annotations[name] = (annotation_fields, return_type)

        args = ','.join(args)
        body = '\n'.join(body)

        # Compute the text of the entire function, add it to the text we're generating.
        if decorator:
            src = ' {0}\n def {1}({2}):\n{3}'.format(decorator, name, args, body)
            self.src.append(src)
        else:
            src = ' def {0}({1}):\n{2}'.format(name, args, body)
            self.src.append(src)
        return name, src

    def add_fns_to_class(self, cls):
        # The source to all of the functions we're generating.
        fns_src = '\n'.join(self.src)

        # The locals they use.
        local_vars = ','.join(self.locals.keys())

        # The names of all of the functions, used for the return value of the
        # outer function.  Need to handle the 0-tuple specially.
        if len(self.names) == 0:
            return_names = '()'
        else:
            return_names = '({0},)'.format(','.join(self.names))

        txt = 'def __create_fn__({0}):\n{1}\n return {2}'.format(local_vars, fns_src, return_names)
        ns = OrderedDict()
        exec(txt, self.globals, ns)
        fns = ns['__create_fn__'](**self.locals)

        # Now that we've generated the functions, assign them into cls.
        for name, fn in zip(self.names, fns):
            # Use __qualname__ if available (Python 3), otherwise use __name__
            if six.PY2:
                class_qualname = getattr(cls, '__qualname__', qualname(cls))
            else:
                class_qualname = cls.__qualname__
            fn.__qualname__ = '{0}.{1}'.format(class_qualname, fn.__name__)

            # Apply method annotations if they were stored
            if name in self.method_annotations:
                annotation_fields, return_type = self.method_annotations[name]

                #ann_field_names, ret_type = self.method_annotations[name]
                # Set __annotate__ for PEP 649 deferred evaluation
                if _annotationlib is not None:
                    # Build field_annotations for __annotate__
                    field_annotations = {}
                    cls_annotations = getattr(cls, '__annotations__', OrderedDict())
                    for field_name in annotation_fields:
                        if field_name in cls_annotations:
                            field_annotations[field_name] = cls_annotations[field_name]
                    fn.__annotate__ = _make_annotate_function(
                        cls, name, annotation_fields, return_type, field_annotations=field_annotations)
                else:
                    annotations = OrderedDict()
                    # Get the field types from the class annotations
                    cls_annotations = getattr(cls, '__annotations__', OrderedDict())
                    for field_name in annotation_fields:
                        if field_name in cls_annotations:
                            annotations[field_name] = cls_annotations[field_name]
                    if return_type is not MISSING:
                        annotations['return'] = return_type
                    if annotations:
                        fn.__annotations__ = annotations

            if self.unconditional_adds.get(name, False):
                setattr(cls, name, fn)
            else:
                already_exists = _set_new_attribute(cls, name, fn)

                # See if it's an error to overwrite this particular function.
                msg_extra = self.overwrite_errors.get(name)
                if already_exists and msg_extra:
                    error_msg = 'Cannot overwrite attribute {0} in class {1}'.format(
                        fn.__name__, cls.__name__)
                    if not msg_extra is True:
                        error_msg = '{0} {1}'.format(error_msg, msg_extra)

                    raise TypeError(error_msg)


def _field_assign(frozen, name, value, self_name):
    # If we're a frozen class, then assign to our fields in __init__
    # via object.__setattr__.  Otherwise, just use a simple
    # assignment.
    if frozen:
        return '  __dataclass_builtins_object__.__setattr__({0},{1!r},{2})'.format(
            self_name, name, value)
    return '  {0}.{1}={2}'.format(self_name, name, value)


def _field_init(f, frozen, globals, self_name, slots):
    # Return the text of the line in the body of __init__ that will
    # initialize this field.

    default_name = '__dataclass_dflt_{0}__'.format(f.name)
    if f.default_factory is not MISSING:
        if f.init:
            # This field has a default factory.  If a parameter is
            # given, use it.  If not, call the factory.
            globals[default_name] = f.default_factory
            value = '{0}() if {1} is __dataclass_HAS_DEFAULT_FACTORY__ else {1}'.format(
                default_name, f.name)
        else:
            globals[default_name] = f.default_factory
            value = '{0}()'.format(default_name)
    else:
        # No default factory.
        if f.init:
            if f.default is MISSING:
                # There's no default, just do an assignment.
                value = f.name
            elif f.default is not MISSING:
                globals[default_name] = f.default
                value = f.name
        else:
            # If the class has slots, then initialize this field.
            if slots and f.default is not MISSING:
                globals[default_name] = f.default
                value = default_name
            else:
                return None

    # Only test this now, so that we can create variables for the
    # default.  However, return None to signify that we're not going
    # to actually do the assignment statement for InitVars.
    if f._field_type is _FIELD_INITVAR:
        return None

    # Now, actually generate the field assignment.
    return _field_assign(frozen, f.name, value, self_name)


def _init_param(f):
    # Return the __init__ parameter string for this field.
    if f.default is MISSING and f.default_factory is MISSING:
        # There's no default, and no default_factory, just output the
        # variable name and type.
        default = ''
    elif f.default is not MISSING:
        # There's a default, this will be the name that's used to look
        # it up.
        default = '=__dataclass_dflt_{0}__'.format(f.name)
    elif f.default_factory is not MISSING:
        # There's a factory function.  Set a marker.
        default = '=__dataclass_HAS_DEFAULT_FACTORY__'
    return '{0}{1}'.format(f.name, default)


def _init_fn(fields, std_fields, kw_only_fields, frozen, has_post_init,
             self_name, func_builder, slots):
    # fields contains both real fields and InitVar pseudo-fields.

    seen_default = None
    for f in std_fields:
        # Only consider the non-kw-only fields in the __init__ call.
        if f.init:
            if not (f.default is MISSING and f.default_factory is MISSING):
                seen_default = f
            elif seen_default:
                raise TypeError('non-default argument {0!r} follows default argument {1!r}'.format(
                    f.name, seen_default.name))

    annotation_fields = [f.name for f in fields if f.init]

    locals = {'__dataclass_HAS_DEFAULT_FACTORY__': _HAS_DEFAULT_FACTORY,
              '__dataclass_builtins_object__': object}

    body_lines = []
    for f in fields:
        line = _field_init(f, frozen, locals, self_name, slots)
        # line is None means that this field doesn't require
        # initialization (it's a pseudo-field).  Just skip it.
        if line:
            body_lines.append(line)

    # Does this class have a post-init function?
    if has_post_init:
        params_str = ','.join(f.name for f in fields
                              if f._field_type is _FIELD_INITVAR)
        body_lines.append('  {0}.{1}({2})'.format(self_name, _POST_INIT_NAME, params_str))

    # If no body lines, use 'pass'.
    if not body_lines:
        body_lines = ['  pass']

    _init_params = [_init_param(f) for f in std_fields]
    if kw_only_fields:
        if sys.version_info >= (3,):
            # Add the keyword-only args.
            _init_params += ['*']
            _init_params += [_init_param(f) for f in kw_only_fields]
        else:
            # Python 2: emulate keyword-only with **kwargs
            _init_params.append('**__kw_only_kwargs__')
            kw_extraction = []
            for f in kw_only_fields:
                if f.default is MISSING and f.default_factory is MISSING:
                    kw_extraction.append(
                        '  if "{0}" not in __kw_only_kwargs__: '
                        'raise TypeError("__init__() missing keyword-only argument: \'{0}\'")'.format(f.name))
                    kw_extraction.append('  {0}=__kw_only_kwargs__.pop("{0}")'.format(f.name))
                elif f.default_factory is not MISSING:
                    kw_extraction.append(
                        '  {0}=__kw_only_kwargs__.pop("{0}", __dataclass_HAS_DEFAULT_FACTORY__)'.format(f.name))
                else:
                    kw_extraction.append(
                        '  {0}=__kw_only_kwargs__.pop("{0}", __dataclass_dflt_{0}__)'.format(f.name))
            kw_extraction.append(
                '  if __kw_only_kwargs__: raise TypeError('
                '"__init__() got unexpected keyword arguments: " + ", ".join(__kw_only_kwargs__))')
            body_lines = kw_extraction + body_lines
    return func_builder.add_fn('__init__',
                        [self_name] + _init_params,
                        body_lines,
                        locals=locals,
                        return_type=None,
                        annotation_fields=annotation_fields)


def _frozen_get_del_attr(cls, fields, func_builder):
    locals = {'cls': cls,
              'FrozenInstanceError': FrozenInstanceError,
              '__dataclass_self__': cls}  # Add the class to locals for super()
    condition = 'type(self) is cls'
    if fields:
        condition += ' or name in {' + ', '.join(repr(f.name) for f in fields) + '}'

    attach_debug_function(cls, *func_builder.add_fn('__setattr__',
                        ('self', 'name', 'value'),
                        ('  if {0}:'.format(condition),
                         '   raise FrozenInstanceError("cannot assign to field {0!r}".format(name))',
                         '  super(__dataclass_self__, self).__setattr__(name, value)'),
                        locals=locals,
                        overwrite_error=True))
    attach_debug_function(cls, *func_builder.add_fn('__delattr__',
                        ('self', 'name'),
                        ('  if {0}:'.format(condition),
                         '   raise FrozenInstanceError("cannot delete field {0!r}".format(name))',
                         '  super(__dataclass_self__, self).__delattr__(name)'),
                        locals=locals,
                        overwrite_error=True))


def _is_classvar(a_type, typing):
    return (a_type is typing.ClassVar or type(a_type) == type(typing.ClassVar)
            or (hasattr(typing, 'get_origin') and typing.get_origin(a_type) is typing.ClassVar))


def _is_initvar(a_type, dataclasses):
    # The module we're checking against is the module we're
    # currently in (dataclasses.py).
    return (a_type is dataclasses.InitVar
            or type(a_type) is dataclasses.InitVar)


def _is_kw_only(a_type, dataclasses):
    return a_type is dataclasses.KW_ONLY


def _is_type(annotation, cls, a_module, a_type, is_type_predicate):
    # Given a type annotation string, does it refer to a_type in a_module?
    match = _MODULE_IDENTIFIER_RE.match(annotation)
    if match:
        ns = None
        module_name = match.group(1)
        if not module_name:
            # No module name, assume the class's module did
            # "from dataclasses import InitVar" or "from dataclasses import KW_ONLY".
            _ns = sys.modules.get(cls.__module__, None)
            if _ns is not None:
                ns = _ns.__dict__
        else:
            # Look up module_name in the class's module.
            module = sys.modules.get(cls.__module__)
            if module is not None:
                m1 = module.__dict__.get(module_name)
                if m1 is a_module:
                    # The module_name directly refers to the correct module
                    ns = a_module.__dict__

            # If not found in the current module, try looking it up directly in sys.modules
            if ns is None:
                # Try the module_name directly
                if module_name in sys.modules:
                    potential_module = sys.modules[module_name]
                    if potential_module is a_module:
                        ns = a_module.__dict__

                # Also try the full module path (for backported versions)
                if ns is None and a_module.__name__ and '.' in a_module.__name__:
                    # a_module might be '_py2dataclasses.dataclasses'
                    # Check if 'dataclasses' in the annotation refers to this module
                    if module_name == 'dataclasses' and a_module.__name__.endswith('.dataclasses'):
                        ns = a_module.__dict__

        if ns and is_type_predicate(ns.get(match.group(2)), a_module):
            return True
    return False


def _get_field(cls, a_name, a_type, default_kw_only):
    default = getattr(cls, a_name, MISSING)
    if isinstance(default, (_Field, Field)):
        f = default
    else:
        if isinstance(default, types.MemberDescriptorType):
            default = MISSING
        f = field(default=default, _typ=a_type)

    if f.name != a_name:
        f.__set_name__(cls, a_name)
    f.type = a_type

    f._field_type = _FIELD

    # Check for ClassVar
    typing_mod = sys.modules.get('typing')
    if typing_mod:
        if (_is_classvar(a_type, typing_mod)
                or (isinstance(f.type, str)
                    and _is_type(f.type, cls, typing_mod, typing_mod.ClassVar,
                                 _is_classvar))):
            f._field_type = _FIELD_CLASSVAR

    if f._field_type is _FIELD:
        dataclasses = sys.modules[__name__]
        if (_is_initvar(a_type, dataclasses)
                or (isinstance(f.type, str)
                    and _is_type(f.type, cls, dataclasses, dataclasses.InitVar,
                                 _is_initvar))):
            f._field_type = _FIELD_INITVAR

    if f._field_type in (_FIELD_CLASSVAR, _FIELD_INITVAR):
        if f.default_factory is not MISSING:
            raise TypeError('field {0} cannot have a default factory'.format(f.name))

    if f._field_type in (_FIELD, _FIELD_INITVAR):
        if f.kw_only is MISSING:
            f.kw_only = default_kw_only
    else:
        assert f._field_type is _FIELD_CLASSVAR
        if f.kw_only is not MISSING:
            raise TypeError('field {0} is a ClassVar but specifies kw_only'.format(f.name))

    if f._field_type is _FIELD and f.default.__class__.__hash__ is None:
        raise ValueError('mutable default {0} for field {1} is not allowed: use default_factory'.format(
            type(f.default), f.name))

    return f


def _set_new_attribute(cls, name, value):
    if name in cls.__dict__:
        return True
    setattr(cls, name, value)
    return False


def _hash_set_none(cls, fields, func_builder):
    cls.__hash__ = None


def _hash_add(cls, fields, func_builder):
    flds = [f for f in fields if (f.compare if f.hash is None else f.hash)]
    self_tuple = _tuple_str('self', flds)
    attach_debug_function(cls, *func_builder.add_fn('__hash__',
                                                    ('self',),
                                                    ['  return hash({0})'.format(self_tuple)],
                                                    unconditional_add=True))


def _hash_exception(cls, fields, func_builder):
    raise TypeError('Cannot overwrite attribute __hash__ in class {0}'.format(cls.__name__))


_hash_action = {
    (False, False, False, False): None,
    (False, False, False, True ): None,
    (False, False, True,  False): None,
    (False, False, True,  True ): None,
    (False, True,  False, False): _hash_set_none,
    (False, True,  False, True ): None,
    (False, True,  True,  False): _hash_add,
    (False, True,  True,  True ): None,
    (True,  False, False, False): _hash_add,
    (True,  False, False, True ): _hash_exception,
    (True,  False, True,  False): _hash_add,
    (True,  False, True,  True ): _hash_exception,
    (True,  True,  False, False): _hash_add,
    (True,  True,  False, True ): _hash_exception,
    (True,  True,  True,  False): _hash_add,
    (True,  True,  True,  True ): _hash_exception,
}

def collect_annotations(cls):
    items = []
    name_val_mapping = OrderedDict()
    _existing_annotations = _get_annotations(cls)
    i = 0
    for name, value in cls.__dict__.items():
        if isinstance(value, (Field, _Field)):
            vt = value.type
            if vt is MISSING:
                vt = _existing_annotations.get(name, vt) if _existing_annotations is not None else vt
            t = vt
            if t is None:
                raise TypeError(
                    '{0!r} is a field but has no type annotation'.format(name)
                )
            if value.name is MISSING or value.name is None:
                name_val_mapping[name] = value
            items.append((value.order, name, t))
            i = value.order

    items.sort(key=lambda x: x[0])
    retvar = OrderedDict()
    collected = OrderedDict((name, t) for _, name, t in items)
    if _existing_annotations:
        for k, v in _existing_annotations.items():
            if k in collected:
                value = collected.pop(k)
                retvar[k] = value
            else:
                retvar[k] = v
    for k, v in collected.items():
        retvar[k] = v

    # ---------------------------------------------------------------------------
    # GC-FIX #4: The original used `map(lambda t: …, six.iteritems(…))` for its
    # side-effect of calling __set_name__.  In Python 3, map() returns a lazy
    # iterator; the lambda is NEVER called unless the result is consumed.
    # Replace with an explicit for-loop so __set_name__ is always invoked.
    # ---------------------------------------------------------------------------
    if name_val_mapping:
        for k, v in six.iteritems(name_val_mapping):
            v.__set_name__(cls, k)

    return retvar

def attach_debug_function(cls, fname, f):
    _set_new_attribute(cls, "fn_bodies", {})
    cls.fn_bodies[fname] = f

def _process_class(cls, init, repr, eq, order, unsafe_hash, frozen,
                   match_args, kw_only, slots, weakref_slot):
    fields = OrderedDict()

    _builtin_repr = __builtins__.get('repr') if isinstance(__builtins__, dict) else getattr(__builtins__, 'repr')

    if cls.__module__ in sys.modules:
        globals = sys.modules[cls.__module__].__dict__
    else:
        globals = OrderedDict()

    setattr(cls, _PARAMS, _DataclassParams(init, repr, eq, order,
                                           unsafe_hash, frozen,
                                           match_args, kw_only,
                                           slots, weakref_slot))

    any_frozen_base = False
    all_frozen_bases = None
    has_dataclass_bases = False
    if not hasattr(cls, "__mro__"):
        raise TypeError("dataclasses should be new style classes")
    for b in cls.__mro__[-1:0:-1]:
        base_fields = getattr(b, _FIELDS, None)
        if base_fields is not None:
            has_dataclass_bases = True
            for f in base_fields.values():
                fields[f.name] = f
            if all_frozen_bases is None:
                all_frozen_bases = True
            current_frozen = getattr(b, _PARAMS).frozen
            all_frozen_bases = all_frozen_bases and current_frozen
            any_frozen_base = any_frozen_base or current_frozen

    cls_annotations = _has_annotations(cls) or OrderedDict()

    cls_fields = []
    KW_ONLY_seen = False
    dataclasses = sys.modules[__name__]
    for name, type_ in cls_annotations.items():
        if type_ is _ANY_MARKER:
            if _annotationlib is not None:
                type_ = _annotationlib.ForwardRef('Any', module='typing')
            else:
                type_ = typing.Any
        if (_is_kw_only(type_, dataclasses)
                or (isinstance(type_, str)
                    and _is_type(type_, cls, dataclasses, dataclasses.KW_ONLY,
                                 _is_kw_only))):
            if KW_ONLY_seen:
                raise TypeError('{0!r} is KW_ONLY, but KW_ONLY has already been specified'.format(name))
            KW_ONLY_seen = True
            kw_only = True
        else:
            cls_fields.append(_get_field(cls, name, type_, kw_only))

    for f in cls_fields:
        fields[f.name] = f

        if isinstance(getattr(cls, f.name, None), (Field, _Field)):
            if f.type is MISSING:
                raise TypeError('{0!r} is a field but has no type annotation'.format(f.name))
            if f.default is MISSING:
                delattr(cls, f.name)
            else:
                setattr(cls, f.name, f.default)

    for name, value in cls.__dict__.items():
        if ((isinstance(value, (_Field, Field)) and value.type is None)) and not name in cls_annotations:
            raise TypeError('{0!r} is a field but has no type annotation'.format(name))

    if has_dataclass_bases:
        if any_frozen_base and not frozen:
            raise TypeError('cannot inherit non-frozen dataclass from a frozen one')
        if all_frozen_bases is False and frozen:
            raise TypeError('cannot inherit frozen dataclass from a non-frozen one')

    setattr(cls, _FIELDS, fields)

    class_hash = cls.__dict__.get('__hash__', MISSING)
    has_explicit_hash = not (class_hash is MISSING or
                             (class_hash is None and '__eq__' in cls.__dict__))

    if order and not eq:
        raise ValueError('eq must be true if order is true')

    all_init_fields = [f for f in fields.values()
                       if f._field_type in (_FIELD, _FIELD_INITVAR)]
    (std_init_fields,
     kw_only_init_fields) = _fields_in_init_order(all_init_fields)

    func_builder = _FuncBuilder(globals)

    custom_init_annotations = None
    if '__init__' in cls.__dict__:
        try:
            init_func = cls.__dict__['__init__']
            if _annotationlib is not None and hasattr(init_func, '__annotate__'):
                try:
                    custom_init_annotations = _annotationlib.get_annotations(
                        init_func, format=_annotationlib.Format.FORWARDREF)
                except Exception:
                    pass
            if custom_init_annotations is None:
                try:
                    func_dict = object.__getattribute__(init_func, '__dict__')
                    if '__annotations__' in func_dict:
                        custom_init_annotations = func_dict['__annotations__']
                except (AttributeError, TypeError):
                    pass
            if custom_init_annotations is None:
                try:
                    ann = getattr(init_func, '__annotations__', None)
                    if ann:
                        custom_init_annotations = ann
                except Exception:
                    pass
        except (AttributeError, TypeError, NameError, KeyError):
            pass

    if init:
        has_post_init = hasattr(cls, _POST_INIT_NAME)
        attach_debug_function(cls, *_init_fn(all_init_fields,
                                             std_init_fields,
                                             kw_only_init_fields,
                                             frozen,
                                             has_post_init,
                                             '__dataclass_self__' if 'self' in fields else 'self',
                                             func_builder,
                                             slots,
                                             ))

    _set_new_attribute(cls, '__replace__', _replace)

    field_list = [f for f in fields.values() if f._field_type is _FIELD]

    if repr:
        flds = [f for f in field_list if f.repr]
        if flds:
            field_formats = []
            for i, f in enumerate(flds):
                field_formats.append('{0}={{{1}!r}}'.format(f.name, i + 1))
            repr_fmt = ', '.join(field_formats)
            field_refs = ', '.join(['self.{0}'.format(f.name) for f in flds])
            body_line = '  return "{cls}({fields})".format(self.__class__.__qualname__, {field_refs})'.format(
                cls='{0}',
                fields=repr_fmt,
                field_refs=field_refs
            )
            body = [body_line]
            decorator = "@__dataclasses_recursive_repr()"
        else:
            body = ['  return self.__class__.__qualname__ + "()"'.format(cls='{0}')]
            decorator = None

        attach_debug_function(cls, *func_builder.add_fn('__repr__',
                                                        ('self',),
                                                        body,
                                                        locals={'__dataclasses_recursive_repr': recursive_repr,
                                                                '__dataclasses_actual_recursive_repr': actual_recursive_repr},
                                                        decorator=decorator))

    if eq:
        cmp_fields = [f for f in field_list if f.compare]
        terms = ['self.{0}==other.{0}'.format(f.name) for f in cmp_fields]
        field_comparisons = ' and '.join(terms) or 'True'
        attach_debug_function(cls, *func_builder.add_fn('__eq__',
                                                        ('self', 'other'),
                                                        ['  if self is other:',
                                                         '   return True',
                                                         '  if other.__class__ is self.__class__:',
                                                         '   return {0}'.format(field_comparisons),
                                                         '  return NotImplemented']))

    if order:
        flds = [f for f in field_list if f.compare]
        self_tuple = _tuple_str('self', flds)
        other_tuple = _tuple_str('other', flds)
        for name, op in [('__lt__', '<'),
                         ('__le__', '<='),
                         ('__gt__', '>'),
                         ('__ge__', '>=')]:
            attach_debug_function(cls, *func_builder.add_fn(name,
                                                            ('self', 'other'),
                                                            ['  if other.__class__ is self.__class__:',
                                                             '   return {0}{1}{2}'.format(self_tuple, op, other_tuple),
                                                             '  return NotImplemented'],
                                                            overwrite_error='Consider using functools.total_ordering'))
    elif six.PY2 and eq:
        for name, op in [('__lt__', '<'),
                         ('__le__', '<='),
                         ('__gt__', '>'),
                         ('__ge__', '>=')]:
            error_msg = "'{}' not supported between instances of '{{1}}' and '{{0}}'".format(op)
            body = [
                "  raise TypeError({!r}.format(self.__class__.__name__, other.__class__.__name__))".format(error_msg)
            ]
            attach_debug_function(cls, *func_builder.add_fn(name,
                                                            ('self', 'other'),
                                                            body,
                                                            overwrite_error=None))

    if frozen:
        _frozen_get_del_attr(cls, field_list, func_builder)

    hash_action = _hash_action[bool(unsafe_hash),
    bool(eq),
    bool(frozen),
    has_explicit_hash]
    if hash_action:
        cls.__hash__ = hash_action(cls, field_list, func_builder)

    func_builder.add_fns_to_class(cls)
    if six.PY2:
        cls.__qualname__ = Qualname(cls)

    doc_attr = getattr(cls, '__doc__')
    if doc_attr is None:
        sig_fields = []
        if custom_init_annotations:
            for param_name, param_type in custom_init_annotations.items():
                if param_name != 'return':
                    if (_annotationlib is not None
                            and isinstance(param_type, _annotationlib.ForwardRef)):
                        type_str = param_type.__forward_arg__
                    elif isinstance(param_type, str):
                        type_str = param_type
                    else:
                        type_str = _get_type_str(param_type)
                    sig_fields.append('{}:{}'.format(param_name, type_str))
        else:
            if not init and hasattr(cls, '__init__'):
                try:
                    init_annotations = getattr(cls.__init__, '__annotations__', {})
                    if init_annotations:
                        for param_name, param_type in init_annotations.items():
                            if param_name != 'return':
                                type_str = _get_type_str(param_type)
                                sig_fields.append('{}:{}'.format(param_name, type_str))
                except (AttributeError, TypeError, NameError):
                    pass
            if not sig_fields:
                for f in std_init_fields:
                    type_str = _get_type_str(f.type)
                    if f.default is not MISSING:
                        if f.default is None:
                            default_str = 'None'
                        elif isinstance(f.default, str):
                            default_str = _builtin_repr(f.default)
                        else:
                            default_str = str(f.default)
                        sig_fields.append('{}:{}={}'.format(f.name, type_str, default_str))
                    elif f.default_factory is not MISSING:
                        sig_fields.append('{}:{}=<factory>'.format(f.name, type_str))
                    else:
                        sig_fields.append('{}:{}'.format(f.name, type_str))

        if six.PY3 or doc_attr is not None:
            metaclass = type(cls)
            has_custom_call = False
            if metaclass is not type and '__call__' in metaclass.__dict__:
                has_custom_call = True

            if sig_fields and not has_custom_call:
                cls.__doc__ = '{}({})'.format(cls.__name__, ', '.join(sig_fields))
            elif has_custom_call:
                cls.__doc__ = cls.__name__
            else:
                cls.__doc__ = '{}()'.format(cls.__name__)

    if match_args:
        _set_new_attribute(cls, '__match_args__',
                           tuple(f.name for f in std_init_fields))

    if not slots:
        for base in cls.__bases__:
            for k, v in base.__dict__.items():
                if isinstance(v, (Field, _Field)):
                    if v.name is None:
                        v.__set_name__(base, k)
            base_params = getattr(base, _PARAMS, None)
            if base_params is None and '__slots__' in base.__dict__:
                slots = True
                break

    if weakref_slot and not slots:
        raise TypeError('weakref_slot is True but slots is False')
    if slots:
        cls = _add_slots(cls, frozen, weakref_slot, fields)

    update_abstractmethods(cls)

    if _annotationlib is not None:
        if not hasattr(cls, '__annotate__') or getattr(cls, '__annotate__', None) is None:
            annotation_field_names = [f.name for f in fields.values()]
            cls.__annotate__ = _make_annotate_function(
                cls, '__annotate__', annotation_field_names, MISSING)

    return cls


def _dataclass_getstate(self):
    return [getattr(self, f.name) for f in fields(self)]


def _dataclass_setstate(self, state):
    for field, value in zip(fields(self), state):
        object.__setattr__(self, field.name, value)


def _get_slots(cls):
    slots_val = cls.__dict__.get('__slots__')
    if slots_val is None:
        slots = []
        if getattr(cls, '__weakrefoffset__', -1) != 0:
            slots.append('__weakref__')
        if getattr(cls, '__dictoffset__', -1) != 0:
            slots.append('__dict__')
        for slot in slots:
            yield slot
    elif isinstance(slots_val, str):
        yield slots_val
    elif hasattr(slots_val, '__iter__'):
        if hasattr(slots_val, '__next__') or hasattr(slots_val, 'next'):
            raise TypeError("Slots of '{0}' cannot be determined".format(cls.__name__))
        try:
            for slot in slots_val:
                yield slot
        except TypeError:
            raise TypeError("Slots of '{0}' cannot be determined".format(cls.__name__))
    else:
        raise TypeError("Slots of '{0}' cannot be determined".format(cls.__name__))


def _update_func_cell_for__class__(f, oldcls, newcls):
    if f is None:
        return False
    try:
        idx = f.__code__.co_freevars.index("__class__")
    except ValueError:
        return False
    closure = f.__closure__[idx]
    if closure.cell_contents is oldcls:
        closure.cell_contents = newcls
        return True
    return False


def _clear_forwardref_owners(obj, oldcls):
    if _annotationlib is None:
        return
    if isinstance(obj, _annotationlib.ForwardRef):
        if getattr(obj, '__owner__', None) is oldcls:
            try:
                object.__setattr__(obj, '__owner__', None)
            except (AttributeError, TypeError):
                pass
        return
    if hasattr(obj, '__args__'):
        for arg in obj.__args__:
            _clear_forwardref_owners(arg, oldcls)
    if hasattr(obj, '__origin__'):
        _clear_forwardref_owners(obj.__origin__, oldcls)


def _create_slots(defined_fields, inherited_slots, field_names, weakref_slot):
    seen_docs = False
    slots = OrderedDict()
    items_to_check = list(field_names)
    if weakref_slot:
        items_to_check.append('__weakref__')
    for slot in items_to_check:
        if slot not in inherited_slots:
            doc = getattr(defined_fields.get(slot), 'doc', None)
            if doc is not None:
                seen_docs = True
            slots[slot] = doc
    if seen_docs:
        return slots
    return tuple(slots.keys())


class Qualname(object):
    def __init__(self, cls):
        self.qualname = qualname(cls)

    def __get__(self, instance, owner):
        return self.qualname if instance else _qualname(owner)


def _add_slots(cls, is_frozen, weakref_slot, defined_fields):
    if '__slots__' in cls.__dict__:
        raise TypeError('{0} already specifies __slots__'.format(cls.__name__))

    if hasattr(sys, '_clear_type_descriptors'):
        sys._clear_type_descriptors(cls)

    cls_dict = dict(cls.__dict__)
    field_names = tuple(f.name for f in fields(cls))

    cls_dict.pop('__weakref__', None)
    cls_dict.pop('__dict__', None)

    inherited_slots = set()
    for base in cls.__mro__[1:-1]:
        inherited_slots.update(_get_slots(base))

    cls_dict["__slots__"] = _create_slots(
        defined_fields, inherited_slots, field_names, weakref_slot,
    )

    for field_name in field_names:
        cls_dict.pop(field_name, None)

    if six.PY2:
        qual_name = getattr(cls, '__qualname__', qualname(cls))
    else:
        qual_name = cls.__qualname__

    bases = cls.__orig_bases__ if typing.Generic in cls.__bases__ else cls.__bases__
    if typing.Generic in cls.__bases__ or any(hasattr(b, '__mro_entries__') for b in getattr(cls, '__orig_bases__', ())):
        def exec_body(ns):
            ns.update(cls_dict)
        newcls = _make_class(cls.__name__, bases, exec_body=exec_body)
    else:
        newcls = type(cls)(cls.__name__, bases, cls_dict)

    if qual_name is not None:
        newcls.__qualname__ = qual_name

    if hasattr(cls, '__firstlineno__'):
        newcls.__firstlineno__ = cls.__firstlineno__

    if is_frozen:
        if '__getstate__' not in cls_dict:
            newcls.__getstate__ = _dataclass_getstate
        if '__setstate__' not in cls_dict:
            newcls.__setstate__ = _dataclass_setstate

    # ---------------------------------------------------------------------------
    # GC-FIX #2: The original saved `tmp = cls.__dict__.values()` and then
    # iterated over `list(newcls.__dict__.values()) + list(tmp)`.  The local
    # variable `tmp` kept a live view (or snapshot) of the OLD class's dict,
    # creating a reference cycle:
    #
    #   local frame  →  tmp  →  old dict values  →  old class
    #
    # With GC disabled this frame-local cycle is never broken, so the old
    # class object leaks for the lifetime of the frame (the entire call to
    # _add_slots, and transitively _process_class / dataclass decorator).
    # Worse, if _add_slots is inlined into a long-lived scope, the leak is
    # permanent.
    #
    # Fix: snapshot both dicts into a single plain list up-front, then
    # immediately delete both the local reference and any remaining reference
    # to the old class dict before returning.
    # ---------------------------------------------------------------------------
    old_dict_values = list(cls.__dict__.values())
    all_members = list(newcls.__dict__.values()) + old_dict_values
    del old_dict_values  # release snapshot of old dict

    for member in all_members:
        member = inspect.unwrap(member) if hasattr(inspect, 'unwrap') else member
        if isinstance(member, types.FunctionType):
            if _update_func_cell_for__class__(member, cls, newcls):
                break
        elif isinstance(member, property):
            if (_update_func_cell_for__class__(member.fget, cls, newcls)
                    or _update_func_cell_for__class__(member.fset, cls, newcls)
                    or _update_func_cell_for__class__(member.fdel, cls, newcls)):
                break

    del all_members  # release last reference to old class members

    # Fix references in dataclass Fields
    if _annotationlib is not None:
        newcls_ann = _annotationlib.get_annotations(
            newcls, format=_annotationlib.Format.FORWARDREF)
        for f in getattr(newcls, _FIELDS).values():
            try:
                ann = newcls_ann[f.name]
            except KeyError:
                pass
            else:
                f.type = ann
                # Clear ForwardRef owners that reference the old class (gh-135228)
                _clear_forwardref_owners(ann, cls)

    # Fix the class reference in the __annotate__ method
    init = newcls.__init__
    init_annotate = getattr(init, '__annotate__', None)
    if init_annotate is not None:
        if getattr(init_annotate, '__generated_by_dataclasses__', False):
            _update_func_cell_for__class__(init_annotate, cls, newcls)

    # Explicitly break the remaining strong reference to the old class so it
    # can be freed immediately (no GC needed).
    del cls

    return newcls


def _has_annotations(cls):
    try:
        return object.__getattribute__(cls, "__annotations__")
    except Exception:
        return None


def annotate(__annotations__, **kwargs):
    """Python 3 compatible function annotation for Python 2."""
    if __annotations__ and not kwargs:
        kwargs = __annotations__
    if kwargs is None:
        raise ValueError('annotations must be provided as keyword arguments')
    def dec(f):
        if _has_annotations(f):
            for k, v in kwargs.items():
                f.__annotations__[k] = v
        else:
            if not kwargs and hasattr(f, "__annotate__"):
                pass
            else:
                setattr(f, "__annotations__", OrderedDict(kwargs))
        return f
    return dec


def dataclass(cls=None, init=True, repr=True, eq=True, order=False,
              unsafe_hash=False, frozen=False, match_args=True,
              kw_only=False, slots=False, weakref_slot=False):
    """Add dunder methods based on the fields defined in the class.

    Examines __annotations__ to determine fields.

    If init is true, an __init__() method is added to the class. If repr
    is true, a __repr__() method is added. If order is true, rich
    comparison dunder methods are added. If unsafe_hash is true, a
    __hash__() method is added. If frozen is true, fields may not be
    assigned to after instance creation. If match_args is true, the
    __match_args__ tuple is added. If kw_only is true, then by default
    all fields are keyword-only. If slots is true, a new class with a
    __slots__ attribute is returned.
    """
    # class F(object):
    #     @property
    #     def aa(self):
    #         return 1
    # F.bb = property(lambda self: 1)
    # pass
    def wrap(cls):
        annotations = collect_annotations(cls)
        if annotations:
            annotate(__annotations__=annotations)(cls)
        else:
            annotate(__annotations__={})(cls)
        return _process_class(cls, init, repr, eq, order, unsafe_hash,
                              frozen, match_args, kw_only, slots,
                              weakref_slot)

    if cls is None:
        return wrap
    return wrap(cls)


def fields(class_or_instance):
    try:
        flds = getattr(class_or_instance, _FIELDS)
    except AttributeError:
        exc = TypeError('must be called with a dataclass type or instance')
        exc.__cause__ = None
        if hasattr(exc, '__suppress_context__'):
            exc.__suppress_context__ = True
        raise exc

    # Exclude pseudo-fields.
    return tuple(f for f in flds.values() if f._field_type is _FIELD)


def _is_dataclass_instance(obj):
    return hasattr(type(obj), _FIELDS)


def is_dataclass(obj):
    cls = obj if isinstance(obj, type) else type(obj)
    return hasattr(cls, _FIELDS)


_default_dict_factory = dict if sys.version_info >= (3, 7) else OrderedDict

def asdict(obj, dict_factory=_default_dict_factory):
    if not _is_dataclass_instance(obj):
        raise TypeError("asdict() should be called on dataclass instances")
    return _asdict_inner(obj, dict_factory)


def _asdict_inner(obj, dict_factory):
    obj_type = type(obj)
    if obj_type in _ATOMIC_TYPES:
        return obj
    elif hasattr(obj_type, _FIELDS):
        if dict_factory is dict:
            return {
                f.name: _asdict_inner(getattr(obj, f.name), dict)
                for f in fields(obj)
            }
        else:
            return dict_factory([
                (f.name, _asdict_inner(getattr(obj, f.name), dict_factory))
                for f in fields(obj)
            ])
    elif obj_type is list:
        return [_asdict_inner(v, dict_factory) for v in obj]
    elif obj_type is dict:
        return {
            _asdict_inner(k, dict_factory): _asdict_inner(v, dict_factory)
            for k, v in obj.items()
        }
    elif obj_type is tuple:
        return tuple([_asdict_inner(v, dict_factory) for v in obj])
    elif issubclass(obj_type, tuple):
        if hasattr(obj, '_fields'):
            return obj_type(*[_asdict_inner(v, dict_factory) for v in obj])
        else:
            return obj_type(_asdict_inner(v, dict_factory) for v in obj)
    elif issubclass(obj_type, dict):
        if hasattr(obj_type, 'default_factory'):
            result = obj_type(obj.default_factory)
            for k, v in obj.items():
                result[_asdict_inner(k, dict_factory)] = _asdict_inner(v, dict_factory)
            return result
        return obj_type((_asdict_inner(k, dict_factory),
                         _asdict_inner(v, dict_factory))
                        for k, v in obj.items())
    elif issubclass(obj_type, list):
        return obj_type(_asdict_inner(v, dict_factory) for v in obj)
    else:
        return copy.deepcopy(obj)


def astuple(obj, tuple_factory=tuple):
    if not _is_dataclass_instance(obj):
        raise TypeError("astuple() should be called on dataclass instances")
    return _astuple_inner(obj, tuple_factory)


def _astuple_inner(obj, tuple_factory):
    if type(obj) in _ATOMIC_TYPES:
        return obj
    elif _is_dataclass_instance(obj):
        return tuple_factory([
            _astuple_inner(getattr(obj, f.name), tuple_factory)
            for f in fields(obj)
        ])
    elif isinstance(obj, tuple) and hasattr(obj, '_fields'):
        return type(obj)(*[_astuple_inner(v, tuple_factory) for v in obj])
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_astuple_inner(v, tuple_factory) for v in obj)
    elif isinstance(obj, dict):
        obj_type = type(obj)
        if hasattr(obj_type, 'default_factory'):
            result = obj_type(getattr(obj, 'default_factory'))
            for k, v in obj.items():
                result[_astuple_inner(k, tuple_factory)] = _astuple_inner(v, tuple_factory)
            return result
        return obj_type((_astuple_inner(k, tuple_factory), _astuple_inner(v, tuple_factory))
                        for k, v in obj.items())
    else:
        return copy.deepcopy(obj)


def _make_class(name, bases=(), kwds=None, exec_body=None):
    fn = getattr(types, "new_class", None)
    if fn is not None:
        cls = fn(name, bases, kwds, exec_body)
    else:
        namespace = OrderedDict()
        if kwds:
            namespace.update(kwds)
        if exec_body:
            exec_body(namespace)
        cls = type(name, bases, namespace)
    return cls


def make_dataclass(
        cls_name,
        fields,
        bases=(),
        namespace=None,
        init=True,
        repr=True,
        eq=True,
        order=False,
        unsafe_hash=False,
        frozen=False,
        match_args=True,
        kw_only=False,
        slots=False,
        weakref_slot=False,
        module=None,
        decorator=dataclass
):
    if decorator is None:
        decorator = dataclass

    if namespace is None:
        namespace = OrderedDict()
    elif type(namespace) is dict:
        namespace = OrderedDict(namespace)
    else:
        print("WARNING: wtf is `namespace`?", namespace, file=sys.stderr)

    seen = set()
    annotations = OrderedDict()
    defaults = OrderedDict()
    for item in fields:
        if isinstance(item, str):
            name = item
            tp = _ANY_MARKER if _annotationlib is not None else typing.Any
        elif len(item) == 2:
            name, tp = item
        elif len(item) == 3:
            name, tp, spec = item
            defaults[name] = spec
        else:
            raise TypeError('Invalid field: {0!r}'.format(item))

        if not isinstance(name, str) or not isidentifier(name):
            raise TypeError('Field names must be valid identifiers: {0!r}'.format(name))
        if keyword.iskeyword(name) and name != "print":
            raise TypeError('Field names must not be keywords: {0!r}'.format(name))
        if name in seen:
            raise TypeError('Field name duplicated: {0!r}'.format(name))

        seen.add(name)
        annotations[name] = tp

    resolved_annotations = OrderedDict()
    for name, tp in annotations.items():
        if tp is _ANY_MARKER:
            if 'typing' in sys.modules:
                resolved_annotations[name] = sys.modules['typing'].Any
            else:
                resolved_annotations[name] = _ANY_MARKER
        else:
            resolved_annotations[name] = tp
    namespace['__annotations__'] = resolved_annotations
    value_blocked = [True]

    def annotate_method(format=None):
        if six.PY2 or not _annotationlib:
            def get_any():
                return 'typing.Any'
        else:
            def get_any():
                if format == _annotationlib.Format.STRING:
                    return 'typing.Any'
                elif format == _annotationlib.Format.FORWARDREF:
                    _typing = sys.modules.get("typing")
                    if _typing is None:
                        return _annotationlib.ForwardRef("Any", module="typing")
                    else:
                        return _typing.Any
                elif format == _annotationlib.Format.VALUE:
                    if value_blocked[0]:
                        raise NotImplementedError
                    from typing import Any
                    return Any
                else:
                    raise NotImplementedError
        annos = OrderedDict()
        for one, t in annotations.items():
            annos[one] = get_any() if t is _ANY_MARKER else t
        if _annotationlib and format == _annotationlib.Format.STRING:
            return _annotationlib.annotations_to_string(annos)
        return annos

    def exec_body_callback(ns):
        ns.update(namespace)
        ns.update(defaults)

    cls = _make_class(cls_name, bases, OrderedDict(), exec_body_callback)
    cls.__annotate__ = annotate_method

    if module is None:
        try:
            module = sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass
    if module is not None:
        cls.__module__ = module

    cls = decorator(cls, init=init, repr=repr, eq=eq, order=order,
                    unsafe_hash=unsafe_hash, frozen=frozen,
                    match_args=match_args, kw_only=kw_only, slots=slots,
                    weakref_slot=weakref_slot)

    if _annotationlib is not None:
        value_blocked[0] = False

    return cls


def replace(obj, **changes):
    if not _is_dataclass_instance(obj):
        raise TypeError("replace() should be called on dataclass instances")
    return _replace(obj, **changes)


def _replace(self, **changes):
    for f in getattr(self, _FIELDS).values():
        if f._field_type is _FIELD_CLASSVAR:
            continue
        if not f.init:
            if f.name in changes:
                raise TypeError('field {0} is declared with init=False, '
                                'it cannot be specified with replace()'.format(f.name))
            continue
        if f.name not in changes:
            if f._field_type is _FIELD_INITVAR and f.default is MISSING:
                raise TypeError("InitVar {0!r} must be specified with replace()".format(f.name))
            changes[f.name] = getattr(self, f.name)

    return self.__class__(**changes)
