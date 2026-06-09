"""Timed response check — how fast is the current model?"""

import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

from brain.agent import Agent

a = Agent()
for p in ["yo am i your boss or what?", "what time is it"]:
    t = time.time()
    r = a.run(p)
    print(f"\nYOU: {p}\nJARVIS: {r}\n[took {time.time() - t:.1f}s]")
