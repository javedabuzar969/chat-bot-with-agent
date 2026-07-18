import logging
import os
from pathlib import Path

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _describe_entry(entry: Path) -> str:
    if entry.is_dir():
        return f"[DIR] {entry.name}"
    if entry.is_file():
        return f"[FILE] {entry.name}"
    return f"[OTHER] {entry.name}"


@tool
def explore_directory(path: str) -> str:
    """Open a local folder and return a concise list of its contents.

    Use this tool when the user asks to open a folder, inspect files, or
    understand what is inside a specific directory.
    """
    trimmed = (path or "").strip()
    if not trimmed:
        return "Please provide a folder path or name to explore."

    target = Path(trimmed)
    if not target.is_absolute():
        target = Path.cwd() / target

    if not target.exists():
        return f"The folder '{path}' does not exist. Please provide a valid path."
    if not target.is_dir():
        return f"'{path}' is not a folder. Please provide a directory path."

    try:
        if os.name == "nt":
            os.startfile(str(target))
        else:
            # Open the folder on non-Windows systems if possible.
            if os.name == "posix":
                os.system(f"xdg-open '{target}' 2>/dev/null || open '{target}' 2>/dev/null")
    except Exception:
        logger.debug("Could not open folder explorer for %s", target, exc_info=True)

    entries = sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
    directories = [e.name for e in entries if e.is_dir()]
    files = [e.name for e in entries if e.is_file()]

    summary_lines = [f"Opened folder: {target}", f"{len(directories)} directories, {len(files)} files."]
    if directories:
        summary_lines.append("Directories:")
        summary_lines.extend(f"- {name}" for name in directories[:20])
        if len(directories) > 20:
            summary_lines.append(f"- and {len(directories) - 20} more directories...")
    if files:
        summary_lines.append("Files:")
        summary_lines.extend(f"- {name}" for name in files[:20])
        if len(files) > 20:
            summary_lines.append(f"- and {len(files) - 20} more files...")

    return "\n".join(summary_lines)
