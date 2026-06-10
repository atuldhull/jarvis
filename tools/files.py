"""File tools — list, read, search, and manage files. Stdlib only (no pip)."""

import glob
import os

from .registry import tool


@tool(
    "list_dir",
    "List the files and folders in a directory.",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Folder path; defaults to the current folder."}
        },
    },
)
def list_dir(path="."):
    try:
        entries = sorted(os.listdir(path))
    except Exception as e:
        return f"Couldn't list {path}: {e}"
    if not entries:
        return f"{path} is empty."
    return "\n".join(
        ("[dir]  " if os.path.isdir(os.path.join(path, e)) else "[file] ") + e
        for e in entries
    )


@tool(
    "read_text_file",
    "Read a UTF-8 text file (first ~2000 characters).",
    {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
def read_text_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return f.read(2000)
    except Exception as e:
        return f"Couldn't read {path}: {e}"


@tool(
    "find_files",
    "Find files matching a glob pattern (e.g. *.py) under a root folder.",
    {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "e.g. '*.py'"},
            "root": {"type": "string", "description": "Folder to search from; defaults to current."},
        },
        "required": ["pattern"],
    },
)
def find_files(pattern, root="."):
    matches = glob.glob(os.path.join(root, "**", pattern), recursive=True)
    if not matches:
        return f"No files matching {pattern} under {root}."
    return "\n".join(matches[:50])


@tool(
    "make_folder",
    "Create a new folder (and any parent folders).",
    {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
)
def make_folder(path):
    try:
        os.makedirs(path, exist_ok=True)
        return f"Created folder {path}."
    except Exception as e:
        return f"Couldn't create {path}: {e}"


@tool(
    "write_text_file",
    "Write (or overwrite) a UTF-8 text file — used to save code, notes, configs, reports. "
    "Creates parent folders as needed.",
    {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Where to write, e.g. 'app/main.py'."},
            "content": {"type": "string", "description": "The full text to write."},
        },
        "required": ["path", "content"],
    },
)
def write_text_file(path, content):
    try:
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} chars to {path}."
    except Exception as e:
        return f"Couldn't write {path}: {e}"


@tool(
    "delete_file",
    "Delete a file. This is irreversible, so it asks for confirmation first.",
    {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
    confirm=True,
)
def delete_file(path):
    try:
        os.remove(path)
        return f"Deleted {path}."
    except Exception as e:
        return f"Couldn't delete {path}: {e}"
