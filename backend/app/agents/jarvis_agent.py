import logging
from typing import AsyncIterator

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.prebuilt import create_react_agent

from app.agents.tools import explore_directory, open_application, open_url, web_search
from app.config import get_settings
from app.core.llm import get_llm
from app.services.session import get_session_store

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are Jarvis, a helpful, polite, and concise AI assistant running on the user's computer.

Keep spoken-style responses clear and natural, since your output may be read aloud by a text-to-speech engine.
"""

_tools = [web_search, open_url, open_application, explore_directory]


def _build_agent():
    llm = get_llm(streaming=True)
    return create_react_agent(
        llm,
        _tools,
        prompt=SYSTEM_PROMPT,
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
    messages = []
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
