"""Live agent test across several tools — confirms the model picks the right one."""

import sys

sys.stdout.reconfigure(encoding="utf-8")

from brain.agent import Agent


def main():
    a = Agent()
    print("Q (system):", a.run("What operating system and Python version am I running?"))
    a.reset()
    print("Q (files): ", a.run("List the files in the current folder, please."))


if __name__ == "__main__":
    main()
