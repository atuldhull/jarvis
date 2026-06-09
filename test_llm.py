"""Live model checks — needs Ollama running and config.MODEL pulled.

Verifies the two LLM paths:
  1. Brain.think()  — plain chat with the persona.
  2. Agent.run()    — tool-calling (should call get_time and report it back).

Run:  py test_llm.py
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")  # Windows cp1252 → UTF-8

from brain.llm import Brain
from brain.agent import Agent


def main():
    print("=== BRAIN (plain chat) ===")
    print("JARVIS:", Brain().think("Greet me in one short sentence, in character."))

    print("\n=== AGENT (tool-calling: expects a get_time call) ===")
    print("JARVIS:", Agent().run("What is the date and time right now?"))

    print("\nLIVE CHECKS DONE ✅")


if __name__ == "__main__":
    main()
