import abc
import sys
import six
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