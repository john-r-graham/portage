from enum import Enum

class DumpMode(Enum):
    DATA = 'data'
    METHODS = 'methods'

class Settings:
    INDENT_INCREMENT = 4

def dump_attr(name, value, console, indent, max_depth, visited, visited_debug):
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

    # Check for custom __better_repr__ method first
    if hasattr(value, '__better_repr__') and callable(getattr(value, '__better_repr__')):
        # Don't print the type name, just the attribute name and colon
        console.print(indent_str + f"{name}: ", end='')
        # Pass indent + 1 so nested content is properly indented
        value.__better_repr__(console=console, indent=indent + 1, max_depth=max_depth, 
                            visited=visited, visited_debug=visited_debug)
        return

    # Handle collections that need multi-line formatting
    if isinstance(value, dict):
        if not value:  # Empty dict
            console.print(indent_str + f"{name}: {{}}")
            return
        console.print(indent_str + f"{name}: {{")
        next_indent_str = " " * (indent + 1) * Settings.INDENT_INCREMENT
        for k, v in value.items():
            console.print(f"{next_indent_str}{k}: {v}")
        console.print(indent_str + "}")
        return
    elif isinstance(value, (list, tuple, set)):
        if not value:  # Empty collection
            console.print(indent_str + f"{name}: {type(value).__name__}()")
            return
        console.print(indent_str + f"{name}: {type(value).__name__}(")
        next_indent_str = " " * (indent + 1) * Settings.INDENT_INCREMENT
        for item in value:
            console.print(f"{next_indent_str}{item}")
        console.print(indent_str + ")")
        return

    # Handle basic cases
    console.print(indent_str + f"{name}: {value}")
