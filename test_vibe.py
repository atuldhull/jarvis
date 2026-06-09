"""Quick vibe check — does the model swear + roast with the new persona?"""

import sys

sys.stdout.reconfigure(encoding="utf-8")

from brain.llm import Brain

b = Brain()
prompts = [
    "yo",
    "bro i just deleted my entire project folder by accident lmao",
    "i forgot to save my work again and lost 2 hours",
]
for p in prompts:
    print(f"\nYOU: {p}\nJARVIS: {b.think(p)}")
