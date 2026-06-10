"""Confirm-before-irreversible-action guardrail.

Because JARVIS can click things and use real logins, any tool registered with
confirm=True (delete, send, buy, post, log in — anything you can't undo) is routed
through here first. Everything routine (open app, search, tell the time) skips it.

This is deliberately the ONE chokepoint for "are you sure?" so a wrong autonomous
action can't quietly do damage.
"""


import threading

# When the orchestrator runs steps in parallel, two confirm prompts could otherwise
# interleave on the same terminal. This lock makes confirmations strictly one-at-a-time.
_prompt_lock = threading.Lock()


def confirm(action_name, args, who="") -> bool:
    label = f" [{who}]" if who else ""  # which agent/department is asking
    with _prompt_lock:
        print(f"\n⚠️  Sensitive action requested{label}: {action_name}({args})")
        answer = input("    Allow it? type 'yes' to proceed > ").strip().lower()
    return answer in {"yes", "y"}
