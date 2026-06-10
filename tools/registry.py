"""Tool registry — the menu of real actions the model can choose from.

Each tool is a plain Python function wrapped with @tool(...), which records:
  - the name the model calls,
  - a description (the model reads this to decide *when* to use it),
  - a JSON-schema of the arguments,
  - whether the action is sensitive (confirm=True → the safety layer asks first).

The agent loop reads schemas() to tell the model what's on the menu, and uses
dispatch() to actually run whatever the model picked.
"""

_TOOLS = {}


def tool(name, description, parameters=None, confirm=False):
    parameters = parameters or {"type": "object", "properties": {}}

    def wrap(fn):
        _TOOLS[name] = {
            "fn": fn,
            "confirm": confirm,
            "schema": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
        }
        return fn

    return wrap


def schemas(only=None):
    """The tool definitions to hand the model.

    Pass `only=[names]` to expose just a subset — that's how each specialist agent
    is given only the tools for its department. `only=None` returns the full menu.
    """
    if only is None:
        return [t["schema"] for t in _TOOLS.values()]
    allowed = set(only)
    return [t["schema"] for name, t in _TOOLS.items() if name in allowed]


def needs_confirm(name):
    return name in _TOOLS and _TOOLS[name]["confirm"]


def dispatch(name, args):
    """Run the tool the model chose. Returns a string the model reads back."""
    entry = _TOOLS.get(name)
    if entry is None:
        return f"(no such tool: {name})"
    return entry["fn"](**args)


def names():
    return list(_TOOLS)
