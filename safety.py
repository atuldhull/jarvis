"""Confirm-before-irreversible-action guardrail.

Because JARVIS can click things and use real logins, any tool registered with
confirm=True (delete, send, buy, post, log in — anything you can't undo) is routed
through here first. Everything routine (open app, search, tell the time) skips it.

This is deliberately the ONE chokepoint for "are you sure?" so a wrong autonomous
action can't quietly do damage.
"""


def confirm(action_name, args) -> bool:
    print(f"\n⚠️  Sensitive action requested: {action_name}({args})")
    answer = input("    Allow it? type 'yes' to proceed > ").strip().lower()
    return answer in {"yes", "y"}
