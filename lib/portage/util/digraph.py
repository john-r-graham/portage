# Copyright 2010-2014 Gentoo Foundation
# Distributed under the terms of the GNU General Public License v2

__all__ = ["digraph"]

import bisect
from collections import deque

from rich.console import Console
import portage.better_repr

from portage.util import writemsg


class digraph:
    """
    A directed graph object.
    """

    def __init__(self):
        """Create an empty digraph"""

        # { node : ( { child : priority } , { parent : priority } ) }
        self.nodes = {}
        self.order = []

    def add(self, node, parent, priority=0):
        """Adds the specified node with the specified parent.

        If the dep is a soft-dep and the node already has a hard
        relationship to the parent, the relationship is left as hard."""

        if node not in self.nodes:
            self.nodes[node] = ({}, {}, node)
            self.order.append(node)

        if not parent:
            return

        if parent not in self.nodes:
            self.nodes[parent] = ({}, {}, parent)
            self.order.append(parent)

        priorities = self.nodes[node][1].get(parent)
        if priorities is None:
            priorities = []
            self.nodes[node][1][parent] = priorities
            self.nodes[parent][0][node] = priorities

        if not priorities or priorities[-1] is not priority:
            bisect.insort(priorities, priority)

    def discard(self, node):
        """
        Like remove(), except it doesn't raises KeyError if the
        node doesn't exist.
        """
        try:
            self.remove(node)
        except KeyError:
            pass

    def remove(self, node):
        """Removes the specified node from the digraph, also removing
        and ties to other nodes in the digraph. Raises KeyError if the
        node doesn't exist."""

        if node not in self.nodes:
            raise KeyError(node)

        for parent in self.nodes[node][1]:
            del self.nodes[parent][0][node]
        for child in self.nodes[node][0]:
            del self.nodes[child][1][node]

        del self.nodes[node]
        self.order.remove(node)

    def update(self, other):
        """
        Add all nodes and edges from another digraph instance.
        """
        for node in other.order:
            children, parents, node = other.nodes[node]
            if parents:
                for parent, priorities in parents.items():
                    for priority in priorities:
                        self.add(node, parent, priority=priority)
            else:
                self.add(node, None)

    def clear(self):
        """
        Remove all nodes and edges.
        """
        self.nodes.clear()
        del self.order[:]

    def difference_update(self, t):
        """
        Remove all given nodes from node_set. This is more efficient
        than multiple calls to the remove() method.
        """
        if isinstance(t, (list, tuple)) or not hasattr(t, "__contains__"):
            t = frozenset(t)
        order = []
        for node in self.order:
            if node not in t:
                order.append(node)
                continue
            for parent in self.nodes[node][1]:
                del self.nodes[parent][0][node]
            for child in self.nodes[node][0]:
                del self.nodes[child][1][node]
            del self.nodes[node]
        self.order = order

    def has_edge(self, child, parent):
        """
        Return True if the given edge exists.
        """
        try:
            return child in self.nodes[parent][0]
        except KeyError:
            return False

    def remove_edge(self, child, parent):
        """
        Remove edge in the direction from child to parent. Note that it is
        possible for a remaining edge to exist in the opposite direction.
        Any endpoint vertices that become isolated will remain in the graph.
        """

        # Nothing should be modified when a KeyError is raised.
        for k in parent, child:
            if k not in self.nodes:
                raise KeyError(k)

        # Make sure the edge exists.
        if child not in self.nodes[parent][0]:
            raise KeyError(child)
        if parent not in self.nodes[child][1]:
            raise KeyError(parent)

        # Remove the edge.
        del self.nodes[child][1][parent]
        del self.nodes[parent][0][child]

    def __iter__(self):
        return iter(self.order)

    def contains(self, node):
        """Checks if the digraph contains mynode"""
        return node in self.nodes

    def get(self, key, default=None):
        node_data = self.nodes.get(key, self)
        if node_data is self:
            return default
        return node_data[2]

    def all_nodes(self):
        """Return a list of all nodes in the graph"""
        return self.order[:]

    def child_nodes(self, node, ignore_priority=None):
        """Return all children of the specified node"""
        if ignore_priority is None:
            return list(self.nodes[node][0])
        children = []
        if hasattr(ignore_priority, "__call__"):
            for child, priorities in self.nodes[node][0].items():
                for priority in reversed(priorities):
                    if not ignore_priority(priority):
                        children.append(child)
                        break
        else:
            for child, priorities in self.nodes[node][0].items():
                if ignore_priority < priorities[-1]:
                    children.append(child)
        return children

    def parent_nodes(self, node, ignore_priority=None):
        """Return all parents of the specified node"""
        if ignore_priority is None:
            return list(self.nodes[node][1])
        parents = []
        if hasattr(ignore_priority, "__call__"):
            for parent, priorities in self.nodes[node][1].items():
                for priority in reversed(priorities):
                    if not ignore_priority(priority):
                        parents.append(parent)
                        break
        else:
            for parent, priorities in self.nodes[node][1].items():
                if ignore_priority < priorities[-1]:
                    parents.append(parent)
        return parents

    def leaf_nodes(self, ignore_priority=None):
        """Return all nodes that have no children

        If ignore_soft_deps is True, soft deps are not counted as
        children in calculations."""

        leaf_nodes = []
        if ignore_priority is None:
            for node in self.order:
                if not self.nodes[node][0]:
                    leaf_nodes.append(node)
        elif hasattr(ignore_priority, "__call__"):
            for node in self.order:
                is_leaf_node = True
                for child, priorities in self.nodes[node][0].items():
                    for priority in reversed(priorities):
                        if not ignore_priority(priority):
                            is_leaf_node = False
                            break
                    if not is_leaf_node:
                        break
                if is_leaf_node:
                    leaf_nodes.append(node)
        else:
            for node in self.order:
                is_leaf_node = True
                for child, priorities in self.nodes[node][0].items():
                    if ignore_priority < priorities[-1]:
                        is_leaf_node = False
                        break
                if is_leaf_node:
                    leaf_nodes.append(node)
        return leaf_nodes

    def root_nodes(self, ignore_priority=None):
        """Return all nodes that have no parents.

        If ignore_soft_deps is True, soft deps are not counted as
        parents in calculations."""

        root_nodes = []
        if ignore_priority is None:
            for node in self.order:
                if not self.nodes[node][1]:
                    root_nodes.append(node)
        elif hasattr(ignore_priority, "__call__"):
            for node in self.order:
                is_root_node = True
                for parent, priorities in self.nodes[node][1].items():
                    for priority in reversed(priorities):
                        if not ignore_priority(priority):
                            is_root_node = False
                            break
                    if not is_root_node:
                        break
                if is_root_node:
                    root_nodes.append(node)
        else:
            for node in self.order:
                is_root_node = True
                for parent, priorities in self.nodes[node][1].items():
                    if ignore_priority < priorities[-1]:
                        is_root_node = False
                        break
                if is_root_node:
                    root_nodes.append(node)
        return root_nodes

    def __bool__(self):
        return bool(self.nodes)

    def is_empty(self):
        """Checks if the digraph is empty"""
        return len(self.nodes) == 0

    def clone(self):
        clone = digraph()
        clone.nodes = {}
        memo = {}
        for children, parents, node in self.nodes.values():
            children_clone = {}
            for child, priorities in children.items():
                priorities_clone = memo.get(id(priorities))
                if priorities_clone is None:
                    priorities_clone = priorities[:]
                    memo[id(priorities)] = priorities_clone
                children_clone[child] = priorities_clone
            parents_clone = {}
            for parent, priorities in parents.items():
                priorities_clone = memo.get(id(priorities))
                if priorities_clone is None:
                    priorities_clone = priorities[:]
                    memo[id(priorities)] = priorities_clone
                parents_clone[parent] = priorities_clone
            clone.nodes[node] = (children_clone, parents_clone, node)
        clone.order = self.order[:]
        return clone

    def delnode(self, node):
        try:
            self.remove(node)
        except KeyError:
            pass

    def firstzero(self):
        leaf_nodes = self.leaf_nodes()
        if leaf_nodes:
            return leaf_nodes[0]
        return None

    def hasallzeros(self, ignore_priority=None):
        return len(self.leaf_nodes(ignore_priority=ignore_priority)) == len(self.order)

    def debug_print(self, fd=None):
        def output(s):
            writemsg(s, noiselevel=-1, fd=fd)

        for node in self.nodes:
            output(f"{node} ")
            if self.nodes[node][0]:
                output("depends on\n")
            else:
                output("(no children)\n")
            for child, priorities in self.nodes[node][0].items():
                output(f"  {child} ({priorities[-1]})\n")

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

    def bfs(self, start, ignore_priority=None):
        if start not in self:
            raise KeyError(start)

        queue, enqueued = deque([(None, start)]), {start}
        while queue:
            parent, n = queue.popleft()
            yield parent, n
            new = set(self.child_nodes(n, ignore_priority)) - enqueued
            enqueued |= new
            queue.extend([(n, child) for child in new])

    def shortest_path(self, start, end, ignore_priority=None):
        if start not in self:
            raise KeyError(start)
        elif end not in self:
            raise KeyError(end)

        paths = {None: []}
        for parent, child in self.bfs(start, ignore_priority):
            paths[child] = paths[parent] + [child]
            if child == end:
                return paths[child]
        return None

    def get_cycles(self, ignore_priority=None, max_length=None):
        """
        Returns all cycles that have at most length 'max_length'.
        If 'max_length' is 'None', all cycles are returned.
        """
        all_cycles = []
        for node in self.nodes:
            # If we have multiple paths of the same length, we have to
            # return them all, so that we always get the same results
            # even with PYTHONHASHSEED="random" enabled.
            shortest_path = None
            candidates = []
            for child in self.child_nodes(node, ignore_priority):
                path = self.shortest_path(child, node, ignore_priority)
                if path is None:
                    continue
                if not shortest_path or len(shortest_path) >= len(path):
                    shortest_path = path
                    candidates.append(path)
            if shortest_path and (not max_length or len(shortest_path) <= max_length):
                for path in candidates:
                    if len(path) == len(shortest_path):
                        all_cycles.append(path)
        return all_cycles

    def __better_repr__(self, console, indent=0, max_depth=4, mode=portage.better_repr.DumpMode.DATA, visited=None):
        """Enhanced representation with different modes"""
        indent_str = " " * indent * portage.better_repr.Settings.INDENT_INCREMENT

        if visited is None:
            visited = set()

        # Handle circular references
        obj_id = id(self)
        if obj_id in visited:
            console.print(indent_str + "<cycle detected>")
            return
        visited.add(obj_id)

        if indent > max_depth:
            console.print(indent_str + "<max depth reached>")
            visited.discard(obj_id)
            return

        console.print(f"{indent_str}{type(self).__name__}")

        if mode == portage.better_repr.DumpMode.DATA:
            self._dump_data_attributes(console, indent + 1, max_depth, visited)
        elif mode == portage.better_repr.DumpMode.METHODS:
            self._dump_methods_only(console, indent + 1)

        visited.discard(obj_id)

    def _dump_methods_only(self, console, indent):
        """Show only methods, no recursion"""
        indent_str0 = " " * (indent + 0) * portage.better_repr.Settings.INDENT_INCREMENT
        indent_str1 = " " * (indent + 1) * portage.better_repr.Settings.INDENT_INCREMENT
        attrs = {}
        if hasattr(self, '__dict__'):
            attrs.update(self.__dict__)
        # Get methods from dir() too, but avoid internal double-underscore methods
        for name in dir(self):
            if not name.startswith('__') or name in ['__init__', '__str__', '__repr__']:
                if name not in attrs:
                    try:
                        attrs[name] = getattr(self, name)
                    except Exception:
                        pass
        method_attrs = {k: v for k, v in attrs.items() if callable(v)}
        if method_attrs:
            console.print(indent_str0 + f"[Methods: {len(method_attrs)}]")
            for name in sorted(method_attrs.keys()):
                console.print(indent_str1 + name)

    def _dump_data_attributes(self, console, indent, max_depth, visited=None):
        """Show only data attributes with full recursion"""
        indent_str0 = " " * (indent + 0) * portage.better_repr.Settings.INDENT_INCREMENT
        indent_str1 = " " * (indent + 1) * portage.better_repr.Settings.INDENT_INCREMENT
        attrs = {}

        # Get instance attributes
        if hasattr(self, '__dict__'):
            console.print(indent_str0 + f"Found __dict__ with keys: {list(self.__dict__.keys())}")
            attrs.update(self.__dict__)

        # Debug: show what dir() finds
        dir_attrs = [name for name in dir(self) if not name.startswith('_') and name not in attrs]
        if dir_attrs:
            console.print(indent_str0 + f"Additional dir() attributes: {dir_attrs}")

        # Add other attributes from dir() if needed
        for name in dir(self):
            if name not in attrs and not name.startswith('_'):
                try:
                    attrs[name] = getattr(self, name)
                except Exception:
                    pass

        # Filter out callable attributes (methods/functions)
        data_attrs = {}
        for k, v in attrs.items():
            if not callable(v):
                data_attrs[k] = v
            else:
                console.print(indent_str0 + f"Skipping callable: {k}")

        console.print(indent_str1 + f"Final data attributes to dump: {list(data_attrs.keys())}")

        for name, value in sorted(data_attrs.items()):
            self.__dump_attr__(name, value, console, indent + 1, max_depth, visited)

    def __dump_attr__(self, name, value, console, indent, max_depth):
        """Dump individual attributes with special handling"""
        indent_str = " " * indent * portage.better_repr.Settings.INDENT_INCREMENT

        # Check for circular references
        obj_id = id(value)
        if obj_id in visited:
            console.print(indent_str + f"{name}: <cycle detected for {type(value).__name__} object>")
            return

        # Check for custom __better_repr__ method first
        if hasattr(value, '__better_repr__') and callable(getattr(value, '__better_repr__')):
            console.print(indent_str + f"{name}: {type(value).__name__}")
            # Add to visited set before recursive call
            visited.add(obj_id)
            value.__better_repr__(console=console, indent=indent + 1, max_depth=max_depth, visited=visited)
            # Optionally remove from visited set after (depends on your cycle detection strategy)
            return

        # Handle basic cases
        console.print(indent_str + f"{name}: {value}")  # Simple fallback

    # Backward compatibility
    addnode = add
    allnodes = all_nodes
    allzeros = leaf_nodes
    hasnode = contains
    __contains__ = contains
    empty = is_empty
    copy = clone
