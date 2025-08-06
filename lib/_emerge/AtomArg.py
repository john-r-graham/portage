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
        if hasattr(self, '__dict__'):
            attributes = [f"{key}={value!r}" for key, value in self.__dict__.items()]
        else:
            attributes = [f"{key}={getattr(self, key)!r}" for key in dir(self) if not key.startswith('__')]
        return f"{self.__class__.__name__}({', '.join(attributes)})"
