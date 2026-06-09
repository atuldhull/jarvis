"""The tools package — JARVIS's hands.

Importing this package registers every tool and re-exposes the registry helpers
the agent loop needs. Add a new skill = add a function with @tool in one of these
modules (or a new module imported below).
"""

from .registry import schemas, dispatch, needs_confirm, names  # noqa: F401

# Importing these modules runs their @tool decorators, which registers the tools.
from . import system        # noqa: F401,E402
from . import web           # noqa: F401,E402
from . import files         # noqa: F401,E402
from . import memory_tools  # noqa: F401,E402

# Browser tools (Phase 3) need Playwright. Importing is safe even before it's
# installed — the import just no-ops, and the tools simply won't be on the menu.
try:
    from . import browser  # noqa: F401,E402
except Exception:
    pass
