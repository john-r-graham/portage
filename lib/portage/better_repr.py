from enum import Enum

class DumpMode(Enum):
    DATA = 'data'
    METHODS = 'methods'

class Settings:
    INDENT_INCREMENT = 4
    MAX_DEPTH=16

class Flags:
    PRINT_LINE_NUMBERS    = 1
    NO_PRINT_LINE_NUMBERS = 2
    DUMP_DATA             = 4
    DUMP_METHODS          = 8

class BetterRepr:
    def __init__(context, console, mode=DumpMode.DATA, flags=0):
        context.console = console
        context.mode = mode
        context.flags = flags
        context.visited = set()
        context.visited_debug = {}
        context.object_registry = {}
        context.line_number = 1
        context.indent=1

    def _print(context, *args, **kwargs):
        """
        Wrapper for console.print that tracks line numbers.
        """
        if context.flags & Flags.PRINT_LINE_NUMBERS:
            context.console.print(f"{context.line_number:>8}: ", end='')
        context.console.print(*args, **kwargs)

        # Count newlines in the output to track line numbers
        text = str(args[0])
        context.line_number += str(args[0]).count('\n')
        if kwargs.get('end', '\n') == '\n':
            context.line_number += 1

    def _better_repr_core(context, object):
        """Enhanced representation with different modes"""
        indent_str = " " * context.indent * Settings.INDENT_INCREMENT
        # Handle circular references
        obj_id = id(object)
        # context._print(f"DEBUG [__better_repr__]: Checking cycle for {type(context).__name__} (ID {obj_id}) - in visited: {obj_id in visited}")
        if obj_id in context.visited:
            context._print(indent_str + f"<cycle detected> - object ID {obj_id}")
            # context._print(f"DEBUG: First encountered at: {visited_debug.get(obj_id, 'Unknown')}")
            return

        context.visited.add(obj_id)
        context.visited_debug[obj_id] = f"{type(context).__name__} at indent {context.indent}"
        # context._print(f"DEBUG: Added {type(context).__name__} (ID {obj_id}) to visited set at indent {context.indent}")

        if context.indent > Settings.MAX_DEPTH:
            context._print(f"{indent_str}  <max depth reached>")
            context.visited.discard(obj_id)
            del context.visited_debug[obj_id]
            return

        context._print(f"{type(object).__name__}")
        if context.mode == DumpMode.DATA:
            context._dump_data_attributes(object)
        elif context.mode == DumpMode.METHODS:
            context._dump_methods_only(object)

        context.visited.discard(obj_id)
        del context.visited_debug[obj_id]

    def _dump_methods_only(context, object):
        """Show only methods, no recursion"""
        indent_str0 = " " * (context.indent + 0) * Settings.INDENT_INCREMENT
        indent_str1 = " " * (context.indent + 1) * Settings.INDENT_INCREMENT
        attrs = {}
        if hasattr(object, '__dict__'):
            attrs.update(object.__dict__)
        # Get methods from dir() too, but avoid internal double-underscore methods
        for name in dir(object):
            if not name.startswith('__') or name in ['__init__', '__str__', '__repr__']:
                if name not in attrs:
                    try:
                        attrs[name] = getattr(object, name)
                    except Exception:
                        pass
        method_attrs = {k: v for k, v in attrs.items() if callable(v)}
        if method_attrs:
            context._print(indent_str0 + f"[Methods: {len(method_attrs)}]")
            for name in sorted(method_attrs.keys()):
                context._print(indent_str1 + name)

    def _dump_data_attributes(context, object):
        """Show only data attributes with full recursion"""
        indent_str = " " * context.indent * Settings.INDENT_INCREMENT
        attrs = {}

        # Get instance attributes
        if hasattr(object, '__dict__'):
            # context._print(indent_str + f"Found __dict__ with keys: {list(context.__dict__.keys())}")
            attrs.update(object.__dict__)

        # Debug: show what dir() finds
        dir_attrs = [name for name in dir(object) if not name.startswith('_') and name not in attrs]
        #if dir_attrs:
        #    context._print(indent_str + f"Additional dir() attributes: {dir_attrs}")

        # Add other attributes from dir() if needed
        for name in dir(object):
            if name not in attrs and not name.startswith('_'):
                try:
                    attrs[name] = getattr(object, name)
                except Exception:
                    pass

        # Filter out callable attributes (methods/functions)
        data_attrs = {}
        for k, v in attrs.items():
            if not callable(v):
                data_attrs[k] = v
            # else:
            #     context._print(indent_str + f"Skipping callable: {k}")

        # context._print(indent_str + f"Final data attributes to dump: {list(data_attrs.keys())}")

        for name, value in sorted(data_attrs.items()):
            context._dump_attr(name, value)

    def _dump_attr(context, name, value):
        """Dump individual attributes with special handling"""
        indent_str = " " * context.indent * Settings.INDENT_INCREMENT

        # Check for circular references
        obj_id = id(value)
        obj_type = type(value)

        # Skip cycle detection for certain immutable/cached types
        if not (obj_type in (bool, type(None)) or 
                (obj_type == int and -5 <= value <= 256)):
            if obj_id in context.visited:
                context._print(indent_str + f"{name}: <cycle detected for {obj_type.__name__} object>")
                return

        # if name in ("metadata", "allowed_keys"):
        #     context._print(indent_str + f"DEBUG: {name} is a {obj_type}")

        # Check for custom __better_repr__ method first
        if hasattr(value, '__better_repr__') and callable(getattr(value, '__better_repr__')):
            # Don't print the type name, just the attribute name and colon
            context._print(indent_str + f"{name}: ", end='')
            # Pass indent + 1 so nested content is properly indented
            value.__better_repr__(context)
            return

        # Handle collections that need multi-line formatting
        if isinstance(value, dict):
            context._dump_dict(name, value)
            return
        elif isinstance(value, (list, tuple, set, frozenset)):
            context._dump_collection(name, value)
            return

        # Handle basic cases
        context._print(indent_str + f"{name}: {repr(value)}")

    def _dump_dict(context, name, value):
        indent_str0 = " " * (context.indent + 0) * Settings.INDENT_INCREMENT
        indent_str1 = " " * (context.indent + 1) * Settings.INDENT_INCREMENT

        name_str = f"{name}: " if name is not None else ""

        if not value:  # Empty dict
            context._print(f"{indent_str0}{name_str}dict {{}}")
            return

        context._print(f"{indent_str0}{name_str}dict {{")

        if context.indent >= Settings.MAX_DEPTH:
            context._print(f"{indent_str0}  <max depth reached>")
            context._print(f"{indent_str0} }}")
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
            k=f"{prefix}{repr(k)}"

            if isinstance(v, dict):
                context.indent += 1
                context._dump_dict(k, v)
                context.indent -= 1
            elif isinstance(v, (list, tuple, set, frozenset)):
                context.indent += 1
                context._dump_collection(k, v)
                context.indent -= 1
            elif hasattr(v, '__better_repr__') and callable(getattr(v, '__better_repr__')):
                context._print(f"{indent_str1}{k}: ", end='')
                context.indent += 2
                v.__better_repr__(context)
                context.indent -= 2
            else:
                context._print(f"{indent_str1}{k}: {v}")

        context._print(indent_str0 + "}")

    def _dump_collection(context, name, value):
        indent_str0 = " " * (context.indent + 0) * Settings.INDENT_INCREMENT
        indent_str1 = " " * (context.indent + 1) * Settings.INDENT_INCREMENT

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

        name_str = f"{name}: " if name is not None else ""

        if not value:  # Empty collection
            context._print(f"{indent_str0}{name_str}{type(value).__name__} {open_delim}{close_delim}")
            return

        context._print(f"{indent_str0}{name_str}{type(value).__name__} {open_delim}")

        if context.indent >= Settings.MAX_DEPTH:
            context._print(f"{indent_str0}  <max depth reached>")
            context._print(f"{indent_str0}{close_delim}")
            return

        for item in value:
            if isinstance(item, dict):
                context.indent += 1
                context._dump_dict(None, item)
                context.indent -= 1
            elif isinstance(item, (list, tuple, set, frozenset)):
                context.indent += 1
                context._dump_collection(None, item)
                context.indent -= 1
            elif hasattr(item, '__better_repr__') and callable(getattr(item, '__better_repr__')):
                # For items with custom __better_repr__, we don't print a name since they're list elements
                context._print(f"{indent_str1}", end='')
                context.indent += 2
                item.__better_repr__(context)
                context.indent -= 2
            else:
                context._print(f"{indent_str1}{repr(item)}")

        context._print(f"{indent_str0}{close_delim}")
