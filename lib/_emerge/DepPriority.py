# Copyright 1999-2023 Gentoo Authors
# Distributed under the terms of the GNU General Public License v2

from _emerge.AbstractDepPriority import AbstractDepPriority


class DepPriority(AbstractDepPriority):
    __slots__ = ("cross", "ignored", "optional", "satisfied")

    def __int__(self):
        """
        Note: These priorities are only used for measuring hardness
        in the circular dependency display via digraph.debug_print(),
        and nothing more. For actual merge order calculations, the
        measures defined by the DepPriorityNormalRange and
        DepPrioritySatisfiedRange classes are used.

        Attributes                            Hardness

        buildtime_slot_op                       0
        buildtime                              -1
        runtime_slot_op                        -2
        runtime                                -3
        runtime_post                           -4
        optional                               -5
        (none of the above)                    -6

        """

        if self.optional:
            return -5
        if self.buildtime_slot_op:
            return 0
        if self.buildtime:
            return -1
        if self.runtime_slot_op:
            return -2
        if self.runtime:
            return -3
        if self.runtime_post:
            return -4
        return -6

    def __str__(self):
        if self.ignored:
            return "ignored"
        if self.optional:
            return "optional"
        if self.buildtime_slot_op:
            return "buildtime_slot_op"
        if self.buildtime:
            return "buildtime"
        if self.runtime_slot_op:
            return "runtime_slot_op"
        if self.runtime:
            return "runtime"
        if self.runtime_post:
            return "runtime_post"
        return "soft"

    def __repr__(self):
        return self._repr_recursive()

    def __repr__(self):
        attrs = [(key, value) for key, value in self.__dict__.items() if not callable(value)]
        attr_strs = []
        for key, value in attrs:
            if hasattr(value, '_repr_recursive'):
                attr_strs.append(f"'{key}': {value._repr_recursive()}")
            elif value is None:
                attr_strs.append(f"'{key}': None")
            elif isinstance(value, bool):
                attr_strs.append(f"'{key}': {value}")
            else:
                attr_strs.append(f"'{key}': {object.__repr__(value)}")
        return f"DepPriority({{{', '.join(attr_strs)}}})"


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
