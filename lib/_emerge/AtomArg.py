# Copyright 1999-2012 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

from portage._sets.base import InternalPackageSet
from _emerge.DependencyArg import DependencyArg


class AtomArg(DependencyArg):
    __slots__ = ("atom", "pset")

    def __init__(self, atom=None, **kwargs):
        DependencyArg.__init__(self, **kwargs)
        self.atom = atom
        self.pset = InternalPackageSet(initial_atoms=(self.atom,), allow_repo=True)

    def __repr__(self):
        return self._repr_recursive()

    def _repr_recursive(self, seen=None):
        if seen is None:
            seen = set()
        if id(self) in seen:
            return f"{self.__class__.__name__}(...)"

        seen.add(id(self))

        if hasattr(self, '__dict__'):
            attrs = [(key, value) for key, value in self.__dict__.items()]
        else:
            attrs = [(key, getattr(self, key)) for key in dir(self) if not key.startswith('__')]
        attr_strs = []
        for key, value in attrs:
            if hasattr(value, '_repr_recursive'):
                if id(value) in seen:
                    attr_strs.append(f"{key}=...")
                else:
                    attr_strs.append(f"{key}={value._repr_recursive(seen)}")
            else:
                attr_strs.append(f"{key}={object.__repr__(value)}")
        return f"{self.__class__.__name__}({', '.join(attr_strs)})"
    
