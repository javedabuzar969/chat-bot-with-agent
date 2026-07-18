import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.agents.jarvis_agent import stream_response
from app.core.stt import transcribe_audio
from app.core.tts import synthesize_speech

logger = logging.getLogger(__name__)

router = APIRouter(tags=["ws"])

# WebSocket message protocol (JSON):
#   Client -> Server:
#     {"type": "text",  "session_id": "abc", "text": "hello jarvis"}
#     {"type": "audio", "session_id": "abc", "filename": "audio.webm",
#      "data": "<base64 audio bytes>"}
#   Server -> Client:
#     {"type": "transcript", "text": "..."}      # only for audio input
#     {"type": "token", "text": "..."}           # streamed reply tokens
#     {"type": "audio", "data": "<base64 mp3>"}  # spoken reply
#     {"type": "done"}
#     {"type": "error", "message": "..."}


@router.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            import base64
            import json

            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_json({"type": "error", "message": "Invalid JSON."})
                continue

            msg_type = msg.get("type")
            session_id = msg.get("session_id", "default")

            if msg_type == "text":
                user_input = (msg.get("text") or "").strip()
            elif msg_type == "audio":
                try:
                    audio = base64.b64decode(msg.get("data", ""))
                    filename = msg.get("filename", "audio.webm")
                    user_input = await transcribe_audio(audio, filename)
                    await websocket.send_json({"type": "transcript", "text": user_input})
                except Exception as exc:  # noqa: BLE001
                    logger.exception("WS STT failed")
                    await websocket.send_json({"type": "error", "message": str(exc)})
                    continue
            else:
                await websocket.send_json(
                    {"type": "error", "message": f"Unknown message type: {msg_type}"}
                )
                continue

            if not user_input:
                await websocket.send_json(
                    {"type": "error", "message": "Empty input after transcription."}
                )
                continue

            full_reply = ""
            async for token in stream_response(session_id, user_input):
                full_reply += token
                await websocket.send_json({"type": "token", "text": token})

            try:
                audio = synthesize_speech(full_reply)
                if audio:
                    await websocket.send_json(
                        {"type": "audio", "data": base64.b64encode(audio).decode()}
                    )
            except Exception as exc:  # noqa: BLE001
                logger.exception("WS TTS failed")
                await websocket.send_json(
                    {"type": "error", "message": f"TTS failed: {exc}"}
                )

            await websocket.send_json({"type": "done"})
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:  # noqa: BLE001
        logger.exception("WebSocket error")
