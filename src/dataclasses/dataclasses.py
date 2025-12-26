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

from abc_utils import update_abstractmethods
from reprlib import recursive_repr, repr as actual_recursive_repr
from string_utils import isidentifier
from cheap_repr import cheap_repr
from class_utils import is_descriptor
from dictproxyhack import dictproxy
import typing
MappingProxyType = dictproxy
GenericAlias = type(typing.List[int])

class DataclassInstance(typing.Protocol):
    __dataclass_fields__= None # type: typing.ClassVar[typing.Dict[str, Field[typing.Any]]]
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


# A sentinel object to detect if a parameter is supplied or not.  Use
# a class to give it a better repr.
class _MISSING_TYPE(object):
    pass

MISSING = _MISSING_TYPE()


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
_ATOMIC_TYPES = frozenset({
    # Common JSON Serializable types
    types.NoneType,
    bool,
    int,
    float,
    str,
    # Other common types
    complex,
    bytes,
    # Other types that are also unaffected by deepcopy
    types.EllipsisType,
    types.NotImplementedType,
    types.CodeType,
    types.BuiltinFunctionType,
    types.FunctionType,
    type,
    range,
    property,
})

# Any marker is used in `make_dataclass` to mark unannotated fields as `Any`
# without importing `typing` module.
_ANY_MARKER = object()

class _GenericMeta(abc.ABCMeta):

    def __getitem__(cls, typ):
        n = type("{}[{}]".format(cls.__name__, typ.__name__), (cls,), {"__origin__":weakref.ref(cls), "__parameters__":typ})

        return n
#f = typing.GenericMeta

class InitVar(object):
    __metaclass__ = _GenericMeta
    __slots__ = ('type',)

    def __init__(self, type_):
        self.type = type_

    def __repr__(self):
        if isinstance(self.type, type):
            type_name = self.type.__name__
        else:
            # typing objects, e.g. List[int]
            type_name = repr(self.type)
        return 'dataclasses.InitVar[{0}]'.format(type_name)

    @classmethod
    def __class_getitem__(cls, type_):
        return InitVar(type_)


# Instances of Field are only ever created from within this module,
# and only from the field() function, although Field instances are
# exposed externally as (conceptually) read-only objects.
class Field(object):
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
        self.order = Field._counter
        Field._counter += 1
        #self.__annotations__["type"];
        self.name = None
        #self.type = None
        self.default = default
        self.default_factory = default_factory
        self.init = init
        self.repr = repr
        self.hash = hash
        self.compare = compare
        self.metadata = (_EMPTY_METADATA
                         if metadata is None else
                         MappingProxyType(metadata))
        self.kw_only = kw_only
        self.doc = doc
        self._field_type = None

    @recursive_repr()
    def __repr__(self):
        return ('{12!s}<{1!s}>(name=({0!r}),'
                'default={2!r},'
                'default_factory={3!r},'
                'init={4!r},'
                'repr={5!r},'
                'hash={6!r},'
                'compare={7!r},'
                'metadata={8!r},'
                'kw_only={9!r},'
                'doc={10!r},'
                '_field_type={11}'
                ')').format(
            self.name, self.type.__name__, self.default, self.default_factory,
            self.init, self.repr, self.hash, self.compare,
            self.metadata, self.kw_only, self.doc, self._field_type, self.__class__)

    def __set_name__(self, owner, name):
        func = getattr(type(self.default), '__set_name__', None)
        if func:
            func(self.default, owner, name)

    __class_getitem__ = classmethod(GenericAlias)


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
          hash=None, compare=True, metadata=None, kw_only=MISSING, doc=None, _cls=Field):
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
    #return field(_typ)
T = typing.TypeVar("T")
def field(_typ=MISSING, default=MISSING, default_factory=MISSING, init=True, repr=True,
                hash=None, compare=True, metadata=None, kw_only=MISSING, doc=None, **kwargs):
    # type: (typing.Type[T], typing.Optional[T], typing.Optional[typing.Callable[[], T]], bool, bool, typing.Optional[bool], bool, typing.Optional[bool], typing.Optional[typing.Mapping[typing.Any, typing.Any]], typing.Optional[str]) -> T
    """

    :rtype: dataclasses.Field
    """
    mode = kwargs["mode"] if "mode" in kwargs else 1
    f = _field(default, default_factory, init, repr, hash, compare,
                  metadata, kw_only, doc, _cls=_oneshot if mode == 1 else Field)
    if _typ == MISSING and default != MISSING:
        _typ = type(default)

    #object.__setattr__(f, "_value_type", _typ)
    f.type = _typ
    return f


# WIP descriptor delegation
class _oneshot(Field):
    def __get__(self, instance, owner):
        if hasattr(self.default, "__get__"):
            v = self.default.__get__(instance, owner)
        else:
            if not instance:
                v = self
            elif self.name and hasattr(instance, self.name):
                v = object.__getattribute__(self, self.name)
            else:
                v = self.default or self.default_factory()
        return v

    def __set__(self, instance, value):
        if hasattr(self.default, "__set__"):
            # descriptor
            self.default.__set__(instance, value)
        elif hasattr(type(self.default), "__set__"):
            # descriptor
            type(self.default).__set__(instance, value)
        elif self.default is value:
            #type(self.default)
            #
            pass
        else:
            raise RuntimeError()
            #f_name = filter(lambda v: v[1] == self, instance.__class__.__dict__.items())
            #if f_name:
            #    setattr(instance, "_{}".format(f_name[0][0]), value)

        #else:
        #    raise RuntimeError()
        #object.__setattr__(instance)
        #self.default.__set__(instance, value)

    def __set_name__(self, owner, name):
        #super(Field).__set_name__(self)
        Field.__set_name__(self, owner, name)
        self.name = name
    #     pass

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
            fn.__qualname__ = '{0}.{1}'.format(cls.__name__, fn.__name__)

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
        # Add the keyword-only args.
        _init_params += ['*']
        _init_params += [_init_param(f) for f in kw_only_fields]
    return func_builder.add_fn('__init__',
                        [self_name] + _init_params,
                        body_lines,
                        locals=locals,
                        return_type=None,
                        annotation_fields=annotation_fields)


def _frozen_get_del_attr(cls, fields, func_builder):
    locals = {'cls': cls,
              'FrozenInstanceError': FrozenInstanceError}
    condition = 'type(self) is cls'
    if fields:
        condition += ' or name in {' + ', '.join(repr(f.name) for f in fields) + '}'

    attach_debug_function(cls, *func_builder.add_fn('__setattr__',
                        ('self', 'name', 'value'),
                        ('  if {0}:'.format(condition),
                         '   raise FrozenInstanceError("cannot assign to field {0!r}".format(name))',
                         '  super({0}, self).__setattr__(name, value)'.format(cls.__name__)),
                        locals=locals,
                        overwrite_error=True))
    attach_debug_function(cls, *func_builder.add_fn('__delattr__',
                        ('self', 'name'),
                        ('  if {0}:'.format(condition),
                         '   raise FrozenInstanceError("cannot delete field {0!r}".format(name))',
                         '  super({0}, self).__delattr__(name)'.format(cls.__name__)),
                        locals=locals,
                        overwrite_error=True))


def _is_classvar(a_type, typing):
    return (a_type is typing.ClassVar
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
            # "from dataclasses import InitVar".
            ns = sys.modules.get(cls.__module__).__dict__
        else:
            # Look up module_name in the class's module.
            module = sys.modules.get(cls.__module__)
            if module and module.__dict__.get(module_name) is a_module:
                ns = sys.modules.get(a_type.__module__).__dict__
        if ns and is_type_predicate(ns.get(match.group(2)), a_module):
            return True
    return False


def _get_field(cls, a_name, a_type, default_kw_only):
    # Return a Field object for this field name and type.

    # If the default value isn't derived from Field, then it's only a
    # normal default value.  Convert it to a Field().
    default = getattr(cls, a_name, MISSING)
    if isinstance(default, Field):
        f = default
    else:
        if isinstance(default, types.MemberDescriptorType):
            # This is a field in __slots__, so it has no default value.
            default = MISSING
        f = field(default=default, _typ=a_type)

    # Only at this point do we know the name and the type.  Set them.
    #f.name = a_name
    f.__set_name__(cls, a_name)
    f.type = a_type

    # Assume it's a normal field until proven otherwise.
    f._field_type = _FIELD

    # Check for ClassVar
    typing = sys.modules.get('typing')
    if typing:
        if (_is_classvar(a_type, typing)
                or (isinstance(f.type, str)
                    and _is_type(f.type, cls, typing, typing.ClassVar,
                                 _is_classvar))):
            f._field_type = _FIELD_CLASSVAR

    # Check for InitVar
    if f._field_type is _FIELD:
        dataclasses = sys.modules[__name__]
        if (_is_initvar(a_type, dataclasses)
                or (isinstance(f.type, str)
                    and _is_type(f.type, cls, dataclasses, dataclasses.InitVar,
                                 _is_initvar))):
            f._field_type = _FIELD_INITVAR

    # Validations for individual fields.
    if f._field_type in (_FIELD_CLASSVAR, _FIELD_INITVAR):
        if f.default_factory is not MISSING:
            raise TypeError('field {0} cannot have a default factory'.format(f.name))

    # kw_only validation and assignment.
    if f._field_type in (_FIELD, _FIELD_INITVAR):
        if f.kw_only is MISSING:
            f.kw_only = default_kw_only
    else:
        assert f._field_type is _FIELD_CLASSVAR
        if f.kw_only is not MISSING:
            raise TypeError('field {0} is a ClassVar but specifies kw_only'.format(f.name))

    # For real fields, disallow mutable defaults.
    if f._field_type is _FIELD and f.default.__class__.__hash__ is None:
        raise ValueError('mutable default {0} for field {1} is not allowed: use default_factory'.format(
            type(f.default), f.name))

    return f


def _set_new_attribute(cls, name, value):
    # Never overwrites an existing attribute.  Returns True if the
    # attribute already exists.
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
    # Raise an exception.
    raise TypeError('Cannot overwrite attribute __hash__ in class {0}'.format(cls.__name__))



_hash_action = {(False, False, False, False): None,
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
    i = 0
    for name, value in cls.__dict__.iteritems():
        if isinstance(value, Field):
            t = value.type
            if t is None:
                raise TypeError(
                    '{0!r} is a field but has no type annotation'.format(name)
                )
            value.__set_name__(cls, name)
            items.append((value.order, name, t))
            i = value.order
        # elif is_descriptor(value):
        #     # TODO: warning here, we shouldn't allow implicit typing
        #     t = type(value)
        #     items.append((i, name, t))
        # i += 1
        # elif not name.startswith("__"):
        #     # TODO: warning here, we shouldn't allow implicit typing
        #     t = type(value)
        #     items.append((i, name, t))
        # i += 1



    items.sort(key=lambda x: x[0])  # sort by descriptor order

    ret = OrderedDict((name, t) for _, name, t in items)
    return ret

def attach_debug_function(cls, fname, f):
    _set_new_attribute(cls, "fn_bodies", {})
    cls.fn_bodies[fname] = f

def _process_class(cls, init, repr, eq, order, unsafe_hash, frozen,
                   match_args, kw_only, slots, weakref_slot):
    fields = OrderedDict()

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

    # Get annotations - in Python 2.7 we expect this to be set by external lib
    cls_annotations = getattr(cls, '__annotations__', OrderedDict())

    # Now find fields in our class.
    cls_fields = []
    KW_ONLY_seen = False
    dataclasses = sys.modules[__name__]
    for name, type_ in cls_annotations.items():
        # See if this is a marker to change the value of kw_only.
        if (_is_kw_only(type_, dataclasses)
                or (isinstance(type_, str)
                    and _is_type(type_, cls, dataclasses, dataclasses.KW_ONLY,
                                 _is_kw_only))):
            if KW_ONLY_seen:
                raise TypeError('{0!r} is KW_ONLY, but KW_ONLY has already been specified'.format(name))
            KW_ONLY_seen = True
            kw_only = True
        else:
            # Otherwise it's a field of some type.
            cls_fields.append(_get_field(cls, name, type_, kw_only))

    for f in cls_fields:
        fields[f.name] = f

        if isinstance(getattr(cls, f.name, None), Field):
            if f.type is MISSING:
                raise TypeError('{0!r} is a field but has no type annotation'.format(f.name))
            if f.default is MISSING:
                delattr(cls, f.name)
            else:
                setattr(cls, f.name, f.default)

    # Do we have any Field members that don't also have annotations?
    for name, value in cls.__dict__.items():
        if ((isinstance(value, Field) and value.type is None)) and not name in cls_annotations:
            raise TypeError('{0!r} is a field but has no type annotation'.format(name))

    # Check rules that apply if we are derived from any dataclasses.
    if has_dataclass_bases:
        if any_frozen_base and not frozen:
            raise TypeError('cannot inherit non-frozen dataclass from a frozen one')

        if all_frozen_bases is False and frozen:
            raise TypeError('cannot inherit frozen dataclass from a non-frozen one')

    # Remember all of the fields on our class (including bases).
    setattr(cls, _FIELDS, fields)

    # Was this class defined with an explicit __hash__?
    class_hash = cls.__dict__.get('__hash__', MISSING)
    has_explicit_hash = not (class_hash is MISSING or
                             (class_hash is None and '__eq__' in cls.__dict__))

    # If we're generating ordering methods, we must be generating the
    # eq methods.
    if order and not eq:
        raise ValueError('eq must be true if order is true')

    # Include InitVars and regular fields (so, not ClassVars).
    all_init_fields = [f for f in fields.values()
                       if f._field_type in (_FIELD, _FIELD_INITVAR)]
    (std_init_fields,
     kw_only_init_fields) = _fields_in_init_order(all_init_fields)

    func_builder = _FuncBuilder(globals)

    if init:
        # Does this class have a post-init function?
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

    # Get the fields as a list, and include only real fields.
    field_list = [f for f in fields.values() if f._field_type is _FIELD]

    if repr:
        flds = [f for f in field_list if f.repr]
        repr_fmt = ', '.join(['{0}={{{1}!r}}'.format(f.name, flds.index(f)) for f in flds])

        #if flds:
        body = ['  return "{0}({1})".format({2})'.format(
            cls.__name__,
            repr_fmt.replace('{', '{{').replace('}', '}}').replace('{{', '{').replace('!r}}', '!r}'),
            ', '.join(['self.{0}'.format(f.name) for f in flds]) if flds else ''
        ).replace(".format()", "")]
        if flds:
            decorator="@__dataclasses_recursive_repr()"
        else:
            decorator = None
        #else:
        #    body = ['  return __dataclasses_actual_recursive_repr(self)']
        #    decorator=None
        attach_debug_function(cls, *func_builder.add_fn('__repr__',
                            ('self',),
                            body,
                            locals={'__dataclasses_recursive_repr':  recursive_repr, '__dataclasses_actual_recursive_repr': actual_recursive_repr},
                            decorator=decorator))
        #_set_new_attribute(cls, "reprbody", f)

    if eq:
        # Create __eq__ method.
        cmp_fields = [field for field in field_list if field.compare]
        terms = ['self.{0}==other.{0}'.format(field.name) for field in cmp_fields]
        field_comparisons = ' and '.join(terms) or 'True'
        attach_debug_function(cls, *func_builder.add_fn('__eq__',
                            ('self', 'other'),
                            ['  if self is other:',
                             '   return True',
                             '  if other.__class__ is self.__class__:',
                             '   return {0}'.format(field_comparisons),
                             '  return NotImplemented']))

    if order:
        # Create and set the ordering methods.
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
    else:
        # Mimic python 3's type errors while comparing different types
        #flds = [f for f in field_list if f.compare]
        #self_tuple = _tuple_str('self', flds)
        #other_tuple = _tuple_str('other', flds)
        for name, op in [('__lt__', '<'),
                         ('__le__', '<='),
                         ('__gt__', '>'),
                         ('__ge__', '>=')]:
            attach_debug_function(cls, *func_builder.add_fn(name,
                                ('self', 'other'),
                                ['  if other.__class__ is self.__class__:',
                                 '   raise TypeError("not supported between instances")',
                                 '  raise TypeError("Mismatched types")'],
                                overwrite_error='not supported between instances'))

    if frozen:
        _frozen_get_del_attr(cls, field_list, func_builder)

    # Decide if/how we're going to create a hash function.
    hash_action = _hash_action[bool(unsafe_hash),
    bool(eq),
    bool(frozen),
    has_explicit_hash]
    if hash_action:
        cls.__hash__ = hash_action(cls, field_list, func_builder)

    # Generate the methods and add them to the class.
    func_builder.add_fns_to_class(cls)

    doc_attr = getattr(cls, '__doc__')
    if doc_attr is None:
        doc_string = ""
    else:
        doc_string = cls.__doc__
    # Create a class doc-string.
    try:
        text_sig = str(", ".join("{}: {!s}".format(k, t.__name__) for k, t in cls.__annotations__.items())).replace(' -> None', '')
    except (TypeError, ValueError, AttributeError):
        text_sig = ''
    doc_string = cls.__name__ + text_sig + doc_string
    if doc_attr is not None:
        cls.__doc__ = doc_string

    if match_args:
        _set_new_attribute(cls, '__match_args__',
                           tuple(f.name for f in std_init_fields))

    # It's an error to specify weakref_slot if slots is False.
    if weakref_slot and not slots:
        raise TypeError('weakref_slot is True but slots is False')
    if slots:
        cls = _add_slots(cls, frozen, weakref_slot, fields)
    #abc.abstractmethod()
    update_abstractmethods(cls)
    return cls


# _dataclass_getstate and _dataclass_setstate are needed for pickling frozen
# classes with slots.
def _dataclass_getstate(self):
    return [getattr(self, f.name) for f in fields(self)]


def _dataclass_setstate(self, state):
    for field, value in zip(fields(self), state):
        # use setattr because dataclass may be frozen
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
    elif hasattr(slots_val, '__iter__') and not hasattr(slots_val, '__next__'):
        for slot in slots_val:
            yield slot
    else:
        raise TypeError("Slots of '{0}' cannot be determined".format(cls.__name__))


def _update_func_cell_for__class__(f, oldcls, newcls):
    # Returns True if we update a cell, else False.
    if f is None:
        return False
    try:
        idx = f.__code__.co_freevars.index("__class__")
    except ValueError:
        return False
    # Fix the cell to point to the new class
    closure = f.__closure__[idx]
    if closure.cell_contents is oldcls:
        closure.cell_contents = newcls
        return True
    return False


def _create_slots(defined_fields, inherited_slots, field_names, weakref_slot):
    # The slots for our class.
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

    # We only return dict if there's at least one doc member
    if seen_docs:
        return slots
    return tuple(slots.keys())


def _add_slots(cls, is_frozen, weakref_slot, defined_fields):
    # Need to create a new class, since we can't set __slots__ after a
    # class has been created.

    # Make sure __slots__ isn't already set.
    if '__slots__' in cls.__dict__:
        raise TypeError('{0} already specifies __slots__'.format(cls.__name__))

    # Create a new dict for our new class.
    cls_dict = dict(cls.__dict__)
    field_names = tuple(f.name for f in fields(cls))

    # Make sure slots don't overlap with those in base classes.
    inherited_slots = set()
    for base in cls.__mro__[1:-1]:
        inherited_slots.update(_get_slots(base))

    cls_dict["__slots__"] = _create_slots(
        defined_fields, inherited_slots, field_names, weakref_slot,
    )

    for field_name in field_names:
        cls_dict.pop(field_name, None)

    # And finally create the class.
    qualname = getattr(cls, '__qualname__', None)
    newcls = type(cls)(cls.__name__, cls.__bases__, cls_dict)
    if qualname is not None:
        newcls.__qualname__ = qualname

    if is_frozen:
        # Need this for pickling frozen classes with slots.
        if '__getstate__' not in cls_dict:
            newcls.__getstate__ = _dataclass_getstate
        if '__setstate__' not in cls_dict:
            newcls.__setstate__ = _dataclass_setstate

    # Fix up any closures which reference __class__.
    for member in newcls.__dict__.values():
        # If this is a wrapped function, unwrap it.
        member = inspect.unwrap(member) if hasattr(inspect, 'unwrap') else member

        if isinstance(member, types.FunctionType):
            if _update_func_cell_for__class__(member, cls, newcls):
                break
        elif isinstance(member, property):
            if (_update_func_cell_for__class__(member.fget, cls, newcls)
                    or _update_func_cell_for__class__(member.fset, cls, newcls)
                    or _update_func_cell_for__class__(member.fdel, cls, newcls)):
                break

    # Fix references in dataclass Fields
    for f in getattr(newcls, _FIELDS).values():
        # In Python 2.7, we don't have sophisticated annotation handling
        pass

    return newcls

def annotate(__annotations__, **kwargs):
    """Python 3 compatible function annotation for Python 2."""
    if __annotations__ and not kwargs:
        kwargs = __annotations__
    if not kwargs:
        raise ValueError('annotations must be provided as keyword arguments')
    def dec(f):
        if hasattr(f, '__annotations__'):
            for k, v in kwargs.items():
                f.__annotations__[k] = v
        else:
            f.__annotations__ = OrderedDict(kwargs)
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

    def wrap(cls):
        annotations = collect_annotations(cls)
        if annotations:
            annotate(__annotations__=annotations)(cls)

        return _process_class(cls, init, repr, eq, order, unsafe_hash,
                              frozen, match_args, kw_only, slots,
                              weakref_slot)

    # See if we're being called as @dataclass or @dataclass().
    if cls is None:
        # We're called with parens.
        return wrap

    # We're called as @dataclass without parens.
    return wrap(cls)


def fields(class_or_instance):
    """Return a tuple describing the fields of this dataclass.

    Accepts a dataclass or an instance of one. Tuple elements are of
    type Field.
    """

    # Might it be worth caching this, per class?
    try:
        fields = getattr(class_or_instance, _FIELDS)
    except AttributeError:
        raise TypeError('must be called with a dataclass type or instance')

    # Exclude pseudo-fields.
    return tuple(f for f in fields.values() if f._field_type is _FIELD)


def _is_dataclass_instance(obj):
    """Returns True if obj is an instance of a dataclass."""
    return hasattr(type(obj), _FIELDS)


def is_dataclass(obj):
    """Returns True if obj is a dataclass or an instance of a
    dataclass."""
    cls = obj if isinstance(obj, type) else type(obj)
    return hasattr(cls, _FIELDS)


def asdict(obj, dict_factory=OrderedDict):
    """Return the fields of a dataclass instance as a new dictionary mapping
    field names to field values.

    Example usage:

      @dataclass
      class C:
          x = None  # with __annotations__ = {'x': int, 'y': int}
          y = None

      c = C(1, 2)
      assert asdict(c) == {'x': 1, 'y': 2}

    If given, 'dict_factory' will be used instead of built-in dict.
    The function applies recursively to field values that are
    dataclass instances. This will also look into built-in containers:
    tuples, lists, and dicts. Other objects are copied with 'copy.deepcopy()'.
    """
    if not _is_dataclass_instance(obj):
        raise TypeError("asdict() should be called on dataclass instances")
    return _asdict_inner(obj, dict_factory)


def _asdict_inner(obj, dict_factory):
    obj_type = type(obj)
    if obj_type in _ATOMIC_TYPES:
        return obj
    elif hasattr(obj_type, _FIELDS):
        # dataclass instance: fast path for the common case
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
    # handle the builtin types first for speed
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
            # obj is a namedtuple
            return obj_type(*[_asdict_inner(v, dict_factory) for v in obj])
        else:
            return obj_type(_asdict_inner(v, dict_factory) for v in obj)
    elif issubclass(obj_type, dict):
        if hasattr(obj_type, 'default_factory'):
            # obj is a defaultdict
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
    """Return the fields of a dataclass instance as a new tuple of field values.

    Example usage:

      @dataclass
      class C:
          x = None  # with __annotations__ = {'x': int, 'y': int}
          y = None

      c = C(1, 2)
      assert astuple(c) == (1, 2)

    If given, 'tuple_factory' will be used instead of built-in tuple.
    The function applies recursively to field values that are
    dataclass instances. This will also look into built-in containers:
    tuples, lists, and dicts. Other objects are copied with 'copy.deepcopy()'.
    """

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
        # obj is a namedtuple
        return type(obj)(*[_astuple_inner(v, tuple_factory) for v in obj])
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_astuple_inner(v, tuple_factory) for v in obj)
    elif isinstance(obj, dict):
        obj_type = type(obj)
        if hasattr(obj_type, 'default_factory'):
            # obj is a defaultdict
            result = obj_type(getattr(obj, 'default_factory'))
            for k, v in obj.items():
                result[_astuple_inner(k, tuple_factory)] = _astuple_inner(v, tuple_factory)
            return result
        return obj_type((_astuple_inner(k, tuple_factory), _astuple_inner(v, tuple_factory))
                        for k, v in obj.items())
    else:
        return copy.deepcopy(obj)


def make_dataclass(
        cls_name, # type: str
        fields, # type: typing.Iterable[typing.Union[str, typing.Tuple[str, typing.Any], typing.Tuple[str, typing.Any, typing.Any]]]
        bases=(), # type: typing.Tuple[type, ...]
        namespace=None, # type: typing.Optional[typing.Dict[str, typing.Any]]
        init=True, # type: bool
        repr=True, # type: bool
        eq=True, # type: bool
        order=False, # type: bool
        unsafe_hash=False, # type: bool
        frozen=False, # type: bool
        match_args=True, # type: bool
        kw_only=False, # type: bool
        slots=False, # type: bool
        weakref_slot=False, # type: bool
        module=None, # type: typing.Optional[str],
        decorator=dataclass # type: typing.Callable[[typing.Type[T], ...], typing.Type[T]]
):
    # type: (...) -> type

    """Return a new dynamically created dataclass.

    The dataclass name will be 'cls_name'.  'fields' is an iterable
    of either (name), (name, type) or (name, type, Field) objects. If type is
    omitted, use the string 'typing.Any'.  Field objects are created by
    the equivalent of calling 'field(name, type [, Field-info])'.

      C = make_dataclass('C', ['x', ('y', int), ('z', int, field(init=False))], bases=(Base,))

    is equivalent to:

      @dataclass
      class C(Base):
          # with __annotations__ = {'x': 'typing.Any', 'y': int, 'z': int}
          z = field(init=False)

    For the bases and namespace parameters, see the builtin type() function.
    """

    if decorator is None:
        decorator = dataclass

    if namespace is None:
        namespace = OrderedDict()
    elif type(namespace) is dict:
        namespace = OrderedDict(namespace)


    # Validate field names
    seen = set()
    annotations = OrderedDict()
    defaults = OrderedDict()
    for item in fields:
        if isinstance(item, str):
            name = item
            tp = _ANY_MARKER
        elif len(item) == 2:
            name, tp = item
        elif len(item) == 3:
            name, tp, spec = item
            defaults[name] = spec
        else:
            raise TypeError('Invalid field: {0!r}'.format(item))

        if not isinstance(name, str) or not isidentifier(name):
            raise TypeError('Field names must be valid identifiers: {0!r}'.format(name))
        if keyword.iskeyword(name):
            raise TypeError('Field names must not be keywords: {0!r}'.format(name))
        if name in seen:
            raise TypeError('Field name duplicated: {0!r}'.format(name))

        seen.add(name)
        annotations[name] = tp

    # Update namespace
    namespace.update(defaults)
    namespace['__annotations__'] = annotations

    # Create the class
    cls = type(cls_name, bases, namespace)

    # Set module
    if module is None:
        try:
            module = sys._getframe(1).f_globals.get('__name__', '__main__')
        except (AttributeError, ValueError):
            pass
    if module is not None:
        cls.__module__ = module

    # Apply the decorator
    cls = decorator(cls, init=init, repr=repr, eq=eq, order=order,
                    unsafe_hash=unsafe_hash, frozen=frozen,
                    match_args=match_args, kw_only=kw_only, slots=slots,
                    weakref_slot=weakref_slot)
    return cls


def replace(obj, **changes):
    """Return a new object replacing specified fields with new values.

    This is especially useful for frozen classes.  Example usage:

      @dataclass(frozen=True)
      class C:
          x = None  # with __annotations__ = {'x': int, 'y': int}
          y = None

      c = C(1, 2)
      c1 = replace(c, x=3)
      assert c1.x == 3 and c1.y == 2
    """
    if not _is_dataclass_instance(obj):
        raise TypeError("replace() should be called on dataclass instances")
    return _replace(obj, **changes)


def _replace(self, **changes):
    # We're going to mutate 'changes', but that's okay because it's a
    # new dict, even if called with 'replace(self, **my_changes)'.

    for f in getattr(self, _FIELDS).values():
        # Only consider normal fields or InitVars.
        if f._field_type is _FIELD_CLASSVAR:
            continue

        if not f.init:
            # Error if this field is specified in changes.
            if f.name in changes:
                raise TypeError('field {0} is declared with init=False, '
                                'it cannot be specified with replace()'.format(f.name))
            continue

        if f.name not in changes:
            if f._field_type is _FIELD_INITVAR and f.default is MISSING:
                raise TypeError("InitVar {0!r} must be specified with replace()".format(f.name))
            changes[f.name] = getattr(self, f.name)

    # Create the new object
    return self.__class__(**changes)