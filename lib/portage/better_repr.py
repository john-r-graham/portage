from enum import Enum

class DumpMode(Enum):
    DATA = 'data'
    METHODS = 'methods'

class Settings:
    INDENT_INCREMENT = 4
    MAX_DEPTH=16

def default_better_repr(self, console, indent=1, mode=DumpMode.DATA, visited=None, visited_debug=None):
    """Enhanced representation with different modes"""
    indent_str = " " * indent * Settings.INDENT_INCREMENT
    if visited is None:
        visited = set()
        visited_debug = {}  # Separate debug tracking

    # Handle circular references
    obj_id = id(self)
    # console.print(f"DEBUG [__better_repr__]: Checking cycle for {type(self).__name__} (ID {obj_id}) - in visited: {obj_id in visited}")
    if obj_id in visited:
        console.print(indent_str + f"<cycle detected> - object ID {obj_id}")
        # console.print(f"DEBUG: First encountered at: {visited_debug.get(obj_id, 'Unknown')}")
        return

    visited.add(obj_id)
    visited_debug[obj_id] = f"{type(self).__name__} at indent {indent}"
    # console.print(f"DEBUG: Added {type(self).__name__} (ID {obj_id}) to visited set at indent {indent}")

    if indent > Settings.MAX_DEPTH:
        console.print(f"{indent_str}  <max depth reached>")
        visited.discard(obj_id)
        del visited_debug[obj_id]
        return

    console.print(f"{type(self).__name__}")
    if mode == DumpMode.DATA:
        _dump_data_attributes(self, console, indent, visited, visited_debug)
    elif mode == DumpMode.METHODS:
        _dump_methods_only(self, console, indent)

    visited.discard(obj_id)
    del visited_debug[obj_id]

def _dump_methods_only(self, console, indent):
    """Show only methods, no recursion"""
    indent_str0 = " " * (indent + 0) * Settings.INDENT_INCREMENT
    indent_str1 = " " * (indent + 1) * Settings.INDENT_INCREMENT
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

def _dump_data_attributes(self, console, indent, visited, visited_debug):
    """Show only data attributes with full recursion"""
    indent_str = " " * indent * Settings.INDENT_INCREMENT
    attrs = {}

    # Get instance attributes
    if hasattr(self, '__dict__'):
        # console.print(indent_str + f"Found __dict__ with keys: {list(self.__dict__.keys())}")
        attrs.update(self.__dict__)

    # Debug: show what dir() finds
    dir_attrs = [name for name in dir(self) if not name.startswith('_') and name not in attrs]
    #if dir_attrs:
    #    console.print(indent_str + f"Additional dir() attributes: {dir_attrs}")

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
        # else:
        #     console.print(indent_str + f"Skipping callable: {k}")

    # console.print(indent_str + f"Final data attributes to dump: {list(data_attrs.keys())}")

    for name, value in sorted(data_attrs.items()):
        dump_attr(name, value, console, indent, visited, visited_debug)

def dump_attr(name, value, console, indent, visited, visited_debug):
    """Dump individual attributes with special handling"""
    indent_str = " " * indent * Settings.INDENT_INCREMENT

    # Check for circular references
    obj_id = id(value)
    obj_type = type(value)

    # Skip cycle detection for certain immutable/cached types
    if not (obj_type in (bool, type(None)) or 
            (obj_type == int and -5 <= value <= 256)):
        if obj_id in visited:
            console.print(indent_str + f"{name}: <cycle detected for {obj_type.__name__} object>")
            return

    # if name in ("metadata", "allowed_keys"):
    #     console.print(indent_str + f"DEBUG: {name} is a {obj_type}")

    # Check for custom __better_repr__ method first
    if hasattr(value, '__better_repr__') and callable(getattr(value, '__better_repr__')):
        # Don't print the type name, just the attribute name and colon
        console.print(indent_str + f"{name}: ", end='')
        # Pass indent + 1 so nested content is properly indented
        value.__better_repr__(console=console, indent=indent + 1, visited=visited, visited_debug=visited_debug)
        return

    # Handle collections that need multi-line formatting
    if isinstance(value, dict):
        _dump_dict(name, value, console, indent, visited, visited_debug)
        return
    elif isinstance(value, (list, tuple, set, frozenset)):
        _dump_collection(name, value, console, indent, visited, visited_debug)
        return

    # Handle basic cases
    console.print(indent_str + f"{name}: {value}")

def _dump_dict(name, value, console, indent, visited, visited_debug):
    indent_str0 = " " * (indent + 0) * Settings.INDENT_INCREMENT
    indent_str1 = " " * (indent + 1) * Settings.INDENT_INCREMENT

    if not value:  # Empty dict
        console.print(f"{indent_str0}{name}: dict {{}}")
        return

    console.print(f"{indent_str0}{name}: dict {{")

    if indent >= Settings.MAX_DEPTH:
        console.print(f"{indent_str0}  <max depth reached>")
        console.print(f"{indent_str0} }}")
        return

    for k, v in value.items():
        if isinstance(k, list):
            prefix = "list"
        elif isinstance(k, tuple):
            prefix = "tuple"
        elif isinstance(k, set):
            prefix = "set"
        elif isinstance(k, frozenset):
            prefix = "frozenset"
        elif isinstance(k, dict):
            prefix = "dict"
        else:
            prefix = ""

        if k == "None":
            console.print(f"{indent_str0}DEBUG: _dump_dict: k == ""None"".")

        k=f"{prefix}{repr(k)}"

        if isinstance(v, dict):
            _dump_dict(k, v, console, indent + 1, visited, visited_debug)
        elif isinstance(v, (list, tuple, set, frozenset)):
            _dump_collection(k, v, console, indent + 1, visited, visited_debug)
        elif hasattr(v, '__better_repr__') and callable(getattr(v, '__better_repr__')):
            console.print(f"{indent_str1}{k}: ", end='')
            v.__better_repr__(console=console, indent=indent + 2, visited=visited, visited_debug=visited_debug)
        else:
            console.print(f"{indent_str1}{k}: {v}")

    console.print(indent_str0 + "}")

def _dump_collection(name, value, console, indent, visited, visited_debug):
    indent_str0 = " " * (indent + 0) * Settings.INDENT_INCREMENT
    indent_str1 = " " * (indent + 1) * Settings.INDENT_INCREMENT

    # Use appropriate brackets based on collection type
    if isinstance(value, list):
        open_delim, close_delim = "[", "]"
    elif isinstance(value, tuple):
        open_delim, close_delim = "(", ")"
    elif isinstance(value, (set, frozenset)):
        open_delim, close_delim = "{", "}"
    else:
        # Fallback for other collection types
        open_delim, close_delim = "(", ")"

    if not value:  # Empty collection
        console.print(f"{indent_str0}{name}: {type(value).__name__} {open_delim}{close_delim}")
        return

    console.print(f"{indent_str0}{name}: {type(value).__name__} {open_delim}")

    if indent >= Settings.MAX_DEPTH:
        console.print(f"{indent_str0}  <max depth reached>")
        console.print(f"{indent_str0}{close_delim}")
        return

    if name is None:
        console.print(f"{indent_str0}DEBUG: _dump_collection: name == ""None"".")

    for item in value:
        if isinstance(item, dict):
            _dump_dict(None, item, console, indent + 1, visited, visited_debug)
        elif isinstance(item, (list, tuple, set, frozenset)):
            _dump_collection(None, item, console, indent + 1, visited, visited_debug)
        elif hasattr(item, '__better_repr__') and callable(getattr(item, '__better_repr__')):
            # For items with custom __better_repr__, we don't print a name since they're list elements
            console.print(f"{indent_str1}", end='')
            item.__better_repr__(console=console, indent=indent + 2, visited=visited, visited_debug=visited_debug)
        else:
            item_str = repr(item) if item is not None else "NoneX"
            console.print(f"{indent_str1}{item_str}")

    console.print(indent_str0 + close_delim)
