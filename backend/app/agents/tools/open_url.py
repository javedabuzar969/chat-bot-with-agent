import logging
from urllib.parse import quote, urlparse

from langchain_core.tools import tool

logger = logging.getLogger(__name__)

# Special prefix the frontend listens for to open URLs in the user's browser.
_OPEN_URL_MARKER = "__OPEN_URL__:"


@tool
def open_url(url: str) -> str:
    """Open a website, web app, or search page in the user's browser.

    Use this for YouTube, Instagram, Google, Facebook, Twitter/X, GitHub, or any web URL/site the user asks to open.
    Accepts full URLs (e.g. 'https://youtube.com') or site names (e.g. 'youtube', 'instagram').
    """
    trimmed = (url or '').strip()
    if not trimmed:
        return 'Please provide a URL or website name to open.'

    # Handle common plain site names without TLDs
    site = trimmed.lower().rstrip('/')
    if site in ('youtube', 'yt'):
        target_url = 'https://www.youtube.com'
    elif site in ('instagram', 'insta', 'ig'):
        target_url = 'https://www.instagram.com'
    elif site in ('google', 'goog'):
        target_url = 'https://www.google.com'
    elif site in ('facebook', 'fb'):
        target_url = 'https://www.facebook.com'
    elif site in ('twitter', 'x'):
        target_url = 'https://x.com'
    elif site in ('github', 'git'):
        target_url = 'https://github.com'
    elif site in ('chatgpt', 'openai'):
        target_url = 'https://chatgpt.com'
    else:
        parsed = urlparse(trimmed)
        if not parsed.scheme:
            trimmed = 'https://' + trimmed
            parsed = urlparse(trimmed)

        # If netloc does not contain a dot (e.g. 'https://something'), append .com
        if parsed.netloc and '.' not in parsed.netloc:
            target_url = f"{parsed.scheme}://{parsed.netloc}.com"
            if parsed.path:
                target_url += parsed.path
            if parsed.query:
                target_url += f"?{parsed.query}"
        else:
            target_url = trimmed

    # Return special marker for frontend to execute window.open()
    return f"{_OPEN_URL_MARKER}{target_url}"
