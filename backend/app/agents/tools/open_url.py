import logging
import os
import shlex
import sys
from urllib.parse import urlparse

from langchain_core.tools import tool

logger = logging.getLogger(__name__)


def _open_with_default_browser(url: str) -> bool:
    try:
        if sys.platform.startswith('win'):
            os.startfile(url)
        elif sys.platform.startswith('darwin'):
            os.system(f"open {shlex.quote(url)}")
        else:
            os.system(f"xdg-open {shlex.quote(url)}")
        return True
    except Exception:
        logger.exception('Failed to open URL %s', url)
        return False


@tool
def open_url(url: str) -> str:
    """Open a website or search page in the default browser.

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

    success = _open_with_default_browser(trimmed)
    if success:
        return f'Opened {trimmed} in your browser.'
    return f'Failed to open {trimmed} in the browser.'
