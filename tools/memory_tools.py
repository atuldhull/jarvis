"""Memory tools — let JARVIS store and recall facts about you on its own."""

from memory.store import Memory

from .registry import tool

_mem = Memory()  # one shared store for the running session


@tool(
    "remember_fact",
    "Store a fact about the user to recall later (e.g. key='name', value='Atul').",
    {
        "type": "object",
        "properties": {
            "key": {"type": "string", "description": "Short label, e.g. 'name' or 'city'."},
            "value": {"type": "string", "description": "The thing to remember."},
        },
        "required": ["key", "value"],
    },
)
def remember_fact(key, value):
    return _mem.remember(key, value)


@tool(
    "recall_fact",
    "Look up a previously remembered fact by its key.",
    {
        "type": "object",
        "properties": {"key": {"type": "string"}},
        "required": ["key"],
    },
)
def recall_fact(key):
    value = _mem.recall(key)
    return value if value is not None else f"(nothing remembered for '{key}')"
