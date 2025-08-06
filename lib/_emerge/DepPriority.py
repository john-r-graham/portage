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
        return self._custom_repr()

    def _custom_repr(self, seen=None, indent=0, indent_step=4):
        """Pretty-printed representation with recursion safety and actual newlines"""
        if seen is None:
            seen = set()
        if id(self) in seen:
            return "DepPriority(...)"
        seen.add(id(self))

        # Collect attributes from slots
        attrs = []
        for attr in self.__slots__:
            if attr.startswith('__') and attr.endswith('__'):
                continue  # Skip special methods
            try:
                value = getattr(self, attr)
                if not callable(value):  # Skip methods
                    attrs.append((attr, value))
            except AttributeError:
                continue  # Skip attributes that raise errors

        # Handle empty case
        if not attrs:
            return "DepPriority({})"

        # Format attributes with indentation
        next_indent = indent + indent_step
        lines = []
        for i, (key, value) in enumerate(attrs):
            # Determine the representation of the value
            if hasattr(value, '_custom_repr'):
                value_repr = value._custom_repr(seen, next_indent, indent_step)
            elif value is None:
                value_repr = 'None'
            elif isinstance(value, bool):
                value_repr = str(value)
            else:
                value_repr = repr(value)

            # Add trailing comma for all but the last item
            suffix = "," if i < len(attrs) - 1 else ""
            lines.append(f"{' ' * next_indent}'{key}': {value_repr}{suffix}")

        # Combine lines with proper indentation and actual newlines
        return (
            f"DepPriority({{'\n' if lines else ''}}\n"
            f"{'\n'.join(lines)}\n"
            f"{' ' * indent}}})"
        )
