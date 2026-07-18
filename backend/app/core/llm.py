from langchain_groq import ChatGroq

from app.config import get_settings


def get_llm(streaming: bool = False) -> ChatGroq:
    """Return a Groq-hosted chat model.

    Groq is used for both the agent LLM and (via the groq SDK) for STT,
    keeping the number of providers and API keys to a minimum.
    """
    settings = get_settings()
    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=settings.groq_chat_temperature,
        streaming=streaming,
    )
