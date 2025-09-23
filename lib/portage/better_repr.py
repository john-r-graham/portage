from enum import Enum

class DumpMode(Enum):
    DATA = 'data'
    METHODS = 'methods'

class Settings:
    INDENT_INCREMENT = 4

def dump_attr(name, value, console, indent, max_depth, visited, visited_debug):
    """Dump individual attributes with special handling"""
    indent_str = " " * indent * portage.better_repr.Settings.INDENT_INCREMENT
    # Check for circular references
    obj_id = id(value)
    # console.print(f"DEBUG [_dump_attr]: Checking cycle for {type(value).__name__} (ID {obj_id}) - in visited: {obj_id in visited}")
    if obj_id in visited:
        console.print(indent_str + f"{name}: <cycle detected for {type(value).__name__} object>")
        # console.print(f"DEBUG: First encountered at: {visited_debug.get(obj_id, 'Unknown')}")
        return

    # Check for custom __better_repr__ method first
    if hasattr(value, '__better_repr__') and callable(getattr(value, '__better_repr__')):
        console.print(indent_str + f"{name}: {type(value).__name__}")
        # Let the object handle its own visited set management
        value.__better_repr__(console=console, indent=indent + 1, max_depth=max_depth, visited=visited, visited_debug=visited_debug)
        return

    # For basic immutable types, don't track in visited set
    if type(value) in (bool, type(None), int, str, float):
        console.print(indent_str + f"{name}: {value}")
        return

    # Handle basic cases - add to visited set to prevent cycles in their references
    visited.add(obj_id)
    visited_debug[obj_id] = f"{type(value).__name__} via {name}"
    # console.print(f"DEBUG: Added {type(value).__name__} (ID {obj_id}) to visited set via {name}")
    console.print(indent_str + f"{name}: {value}")
    # Note: for basic objects, you might want to remove them from visited set after processing
    # depending on your cycle detection strategy
