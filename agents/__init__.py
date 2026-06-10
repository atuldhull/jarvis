"""The agents package — JARVIS OS's org chart.

  Orchestrator (CEO)  →  specialized department agents (roster)  →  tools (employees)

Import the orchestrator and it pulls in the roster; everything thinks through the
model router and shares the tool registry + memory.
"""

from agents.orchestrator import Orchestrator  # noqa: F401
from agents.roster import make_agent, DEPARTMENTS, DEPARTMENT_NAMES, roster_brief  # noqa: F401
