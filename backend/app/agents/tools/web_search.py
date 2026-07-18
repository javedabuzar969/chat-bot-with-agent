from langchain_core.tools import tool

from app.config import get_settings


@tool
def web_search(query: str) -> str:
    """Search the internet for up-to-date information and return a concise summary.

    Use this whenever the user asks about current events, recent facts, live data
    (weather, news, prices, sports scores), or anything you are unsure about.
    Input should be a focused search query string.
    """
    settings = get_settings()
    if not settings.tavily_api_key:
        return "Web search is unavailable: TAVILY_API_KEY is not configured."

    from tavily import TavilyClient

    client = TavilyClient(api_key=settings.tavily_api_key)
    result = client.search(
        query=query,
        max_results=5,
        search_depth="advanced",
        include_answer=True,
    )

    lines = []
    if result.get("answer"):
        lines.append(f"Summary: {result['answer']}")
    for i, item in enumerate(result.get("results", []), 1):
        title = item.get("title", "")
        content = item.get("content", "")
        url = item.get("url", "")
        lines.append(f"{i}. {title}\n   {content}\n   Source: {url}")
    return "\n\n".join(lines) if lines else "No results found."
