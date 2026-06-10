"""Shared JSON extraction — pull the first balanced {...} object out of a model reply.

Small local models wrap JSON in code fences, prose, or trailing examples. This finds
the first complete, balanced object (string-aware, so braces inside strings don't fool
it) and parses it. Used by the planner and the memory capture path alike.
"""

import json


def extract_json(text):
    text = (text or "").strip()
    start = text.find("{")
    if start == -1:
        return None
    depth, in_str, esc = 0, False, False
    for i in range(start, len(text)):
        c = text[i]
        if in_str:
            if esc:
                esc = False
            elif c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        else:
            if c == '"':
                in_str = True
            elif c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    try:
                        return json.loads(text[start:i + 1])
                    except Exception:
                        return None
    return None
