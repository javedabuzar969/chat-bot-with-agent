import logging
import os
import subprocess

from langchain_core.tools import tool

from app.config import get_settings

logger = logging.getLogger(__name__)


@tool
def open_application(name: str) -> str:
    """Open a desktop application on the user's Windows machine by friendly name.

    Supported names include: notepad, calculator, chrome, edge, firefox, explorer,
    cmd, powershell, paint, word, excel, spotify. Pass only the application name,
    not a full command. Returns a short status message.
    """
    settings = get_settings()
    key = (name or "").strip().lower()
    command = settings.app_map.get(key)

    if not command:
        available = ", ".join(sorted(settings.app_map.keys()))
        return (
            f"I don't have '{name}' in my list of known applications. "
            f"Available: {available}."
        )

    try:
        # os.startfile is the most reliable way to launch GUI apps on Windows.
        if os.name == "nt":
            os.startfile(command)  # type: ignore[attr-defined]
        else:
            subprocess.Popen(command, shell=True)
        logger.info("Launched application '%s' via '%s'", name, command)
        return f"Opened {name}."
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to launch %s", name)
        return f"Sorry, I couldn't open {name}: {exc}"
