"""Credential vault — passwords live in Windows Credential Manager via keyring.

Never plain text in a file. JARVIS reads a stored password only when it genuinely
needs to log in, and that path is gated by the safety confirm step. Better still:
prefer the persistent browser profile (log in once by hand) so passwords rarely
need to be typed at all.
"""

import keyring

import config


def set_password(account: str, password: str) -> str:
    keyring.set_password(config.KEYRING_SERVICE, account, password)
    return f"Stored credentials for {account}."


def get_password(account: str):
    return keyring.get_password(config.KEYRING_SERVICE, account)


def delete_password(account: str):
    keyring.delete_password(config.KEYRING_SERVICE, account)
    return f"Removed credentials for {account}."
