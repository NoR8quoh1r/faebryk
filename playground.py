from typing import Protocol, TypeVar, runtime_checkable, _ProtocolMeta
from types import MethodType
from abc import abstractmethod

class Traited:
    def __init__(self, *args, **kwargs):
        self._added_traits = []
        super().__init__(*args, **kwargs)

    def get_traits(self):
        #TODO add inherited traits
        #TODO return value immutable
        return self._added_traits


class _TraitMeta(_ProtocolMeta): # probably a bad idea
    _trait_cls = None

    def __new__(metacls, clsname, bases, attrs):
        if metacls._trait_cls in bases:
            bases += (Protocol,)
        cls = super().__new__(metacls, clsname, bases, attrs) #
        if metacls._trait_cls in bases:
            trait_attrs = {
                k: v
                for (k, v) in attrs.items()
                if getattr(v, "__isabstractmethod__", False)
            }
            T = TypeVar('T', bound=Traited)
            def attached_to(param_cls : type[cls], other : T):# -> Intersection[T, cls]: # Intersection not implemented yet
                assert(not isinstance(other, cls))
                other._added_traits.append(cls)
                for (k, v) in trait_attrs.items():
                    setattr(other, k, param_cls().get_type_description)
                return other
            cls.attached_to = attached_to
            cls = runtime_checkable(cls)
        return cls

class Trait(Protocol, metaclass=_TraitMeta):
    pass

_TraitMeta._trait_cls = Trait

class classproperty(property):
    def __get__(self, cls, owner):
        return classmethod(self.fget).__get__(None, owner)()

class GetTypeDescriptor(Trait):
    @abstractmethod
    def get_type_description(self) -> str:
        raise NotImplementedError

    @classproperty
    def StaticCls(cls):
        if not hasattr(cls, "_static_cls"):
            class _StaticCls(GetTypeDescriptor):
                def __init__(self, type_description, *args, **kwargs):
                    self.type_description = type_description
                    super().__init__(*args, **kwargs)

                def get_type_description(self):
                    return self.type_description

                T = TypeVar('T', bound=Traited)
                @classmethod
                def attached_to(cls, other : T):# -> Intersection[T, GetTypeDescriptor]: # Intersection not implemented yet
                    return GetTypeDescriptor.attached_to(cls, other)
            cls._static_cls = _StaticCls
        return cls._static_cls

    @staticmethod
    def Static(type_description : str) -> 'type[GetTypeDescriptor]':
        class _Static(GetTypeDescriptor.StaticCls):
            def __init__(self):
                super().__init__(type_description)
        return _Static



class Foo(Traited, GetTypeDescriptor.StaticCls):
    def __init__(self):
        super().__init__(type_description="Foo")

foo = Foo()
print(foo.get_type_description())

class Bar(Traited, GetTypeDescriptor.Static("Bar")):
    pass

bar = Bar()
print(bar.get_type_description())

class Baz(Traited):
    pass

baz = Baz()
baz = GetTypeDescriptor.Static("Baz").attached_to(baz)
print(baz.get_type_description())

class Wack(GetTypeDescriptor):
    def __init__(self):
        self.cnt = 0
        super().__init__()

    def get_type_description(self):
        self.cnt += 1
        return str(self.cnt)

baz = Baz()
baz = GetTypeDescriptor.attached_to(Wack, baz)
print(baz.get_type_description())
print(baz.get_type_description())
