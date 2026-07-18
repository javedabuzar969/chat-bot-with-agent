import logging
from typing import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent

from app.agents.tools import explore_directory, open_application, open_url, web_search
from app.config import get_settings
from app.core.llm import get_llm
from app.services.session import get_session_store

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Jarvis, a helpful, concise, and capable AI assistant running on the user's computer.

Your capabilities:
- Answer questions and hold natural conversations.
- Search the internet autonomously with the `web_search` tool whenever you need current, factual, or uncertain information (news, weather, prices, recent events, etc.). Do not say you cannot browse the web — you can search it yourself.
- Open websites or search pages in the browser with the `open_url` tool when the user wants Google, YouTube, or another website opened.
- Open desktop applications for the user with the `open_application` tool when they ask (e.g. "open notepad", "launch chrome").
- Open local folders, inspect their contents, and summarize what is inside using the `explore_directory` tool when the user asks to open or inspect a folder path.
- Use YouTube search language like "search YouTube for" by constructing a YouTube search URL with `open_url` when the user wants videos or tutorials.

Behavior guidelines:
- When the user explicitly asks to open a web page or search site, prefer `open_url` over `web_search`.
- When the user asks to open a local folder or inspect a directory, prefer `explore_directory` and do not use `open_application("explorer")` just to show Quick Access.
- Be proactive: if a question needs live data, search the web without being asked twice.
- Keep spoken-style responses clear and natural, since your output may be read aloud by a text-to-speech engine.
- When you use a tool, briefly acknowledge what you are doing (e.g. "Let me check the web for that.").
- Cite sources from web results when relevant.
- Never invent application names; use only the open_application tool with known names.
"""

_tools = [web_search, open_url, open_application, explore_directory]


def _build_agent():
    llm = get_llm(streaming=True)
    return create_react_agent(
        llm,
        _tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=MemorySaver(),
    )


_agent = None


def get_agent():
    global _agent
    if _agent is None:
        _agent = _build_agent()
    return _agent


async def stream_response(session_id: str, user_input: str) -> AsyncIterator[str]:
    """Stream Jarvis's reply token-by-token for a given session."""
    settings = get_settings()
    store = get_session_store()
    agent = get_agent()

    # Seed conversation memory from the persistent session store.
    history = await store.get_history(session_id)
    messages = [SystemMessage(content=SYSTEM_PROMPT)]
    for role, content in history:
        messages.append(
            HumanMessage(content=content) if role == "user" else AIMessage(content=content)
        )
    messages.append(HumanMessage(content=user_input))

    config = {"configurable": {"thread_id": session_id}}
    collected = ""
    async for chunk in agent.astream({"messages": messages}, config=config):
        # The prebuilt agent yields dicts with a "agent" key containing messages.
        for node, value in chunk.items():
            if node == "agent":
                msg = value.get("messages", [])[-1] if isinstance(value, dict) else None
                if msg and getattr(msg, "content", None):
                    token = msg.content
                    if isinstance(token, str):
                        collected += token
                        yield token

    # Persist the turn for future context.
    await store.append(session_id, "user", user_input)
    await store.append(session_id, "assistant", collected)


async def invoke(session_id: str, user_input: str) -> str:
    """Non-streaming variant: returns the full reply."""
    parts: list[str] = []
    async for token in stream_response(session_id, user_input):
        parts.append(token)
    return "".join(parts)
