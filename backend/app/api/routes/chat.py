import logging

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

from app.agents.jarvis_agent import stream_response
from app.api.deps import require_api_key
from app.schemas import ChatRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat")
async def chat(req: ChatRequest, _: None = Depends(require_api_key)):
    """Stream Jarvis's reply as Server-Sent Events (text/plain token stream)."""

    async def event_publisher():
        try:
            async for token in stream_response(req.session_id, req.message):
                if token.startswith("__ACTION__:open_url:"):
                    url = token[len("__ACTION__:open_url:"):]
                    yield {"event": "open_url", "data": url}
                else:
                    yield {"event": "token", "data": token}
            yield {"event": "done", "data": "[DONE]"}
        except Exception as exc:  # noqa: BLE001
            logger.exception("Chat stream failed")
            yield {"event": "error", "data": str(exc)}

    return EventSourceResponse(event_publisher())
