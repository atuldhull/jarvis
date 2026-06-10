"""Memory tools — let JARVIS store and recall facts about you on its own."""

from memory.store import get_memory

from .registry import tool

_mem = get_memory()  # the process-wide store (shared with the orchestrator's MemoryManager)


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


@tool(
    "search_memory",
    "Search long-term memory by MEANING for things known about the user "
    "(e.g. 'what hardware does he have', 'his preferences'). Use when recall_fact's exact key won't do.",
    {
        "type": "object",
        "properties": {"query": {"type": "string", "description": "What to look up."}},
        "required": ["query"],
    },
)
def search_memory(query):
    hits = _mem.search(query, k=5)
    return "\n".join(f"- {h}" for h in hits) if hits else "(nothing relevant in memory)"
