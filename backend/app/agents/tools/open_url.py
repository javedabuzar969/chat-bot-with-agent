import logging
from urllib.parse import urlparse

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Special prefix the frontend listens for to open URLs in the user's browser.
_OPEN_URL_MARKER = "__OPEN_URL__:"


@tool
def open_url(url: str) -> str:
    """Open a website or search page in the user's browser.

    Use this for Google, YouTube, or any web URL the user wants to visit.
    """
    trimmed = (url or '').strip()
    if not trimmed:
        return 'Please provide a URL or search page to open.'

    parsed = urlparse(trimmed)
    if not parsed.scheme:
        trimmed = 'https://' + trimmed
        parsed = urlparse(trimmed)

    if not parsed.netloc:
        return f"'{url}' is not a valid URL. Please provide a full web address."

    # Return a special marker — the frontend will call window.open() on this.
    return f"{_OPEN_URL_MARKER}{trimmed}"
