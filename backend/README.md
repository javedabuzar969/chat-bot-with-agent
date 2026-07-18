# Jarvis Backend

A production-grade Python backend that powers a **Jarvis**-style AI assistant.

- **Chat** via text or speech (WebSocket + REST)
- **Speech I/O**: Speech-to-Text via Groq Whisper, Text-to-Speech via gTTS
- **Autonomous web search** via Tavily (the agent searches the internet itself)
- **Application control**: opens Windows desktop apps by name
- Built with **FastAPI**, **LangChain / LangGraph**, and **Groq**

## Architecture

```
Client ──WebSocket/REST──> FastAPI
   ├─ STT (Groq Whisper)        [if audio]
   ├─ Jarvis Agent (LangGraph + ChatGroq)
   │     ├─ Tool: web_search (Tavily)
   │     └─ Tool: open_application (os.startfile)
   ├─ Stream text tokens back
   └─ TTS (gTTS) -> mp3 audio stream back
```

## Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
cp .env.example .env          # then fill in GROQ_API_KEY and TAVILY_API_KEY
```

Run locally:

```bash
uvicorn app.main:app --reload --port 8000
```

- API docs: http://localhost:8000/docs
- Health:    http://localhost:8000/health

## Environment variables

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq key (LLM + Whisper STT) |
| `TAVILY_API_KEY` | Tavily key (web search) |
| `API_KEY` | Optional; if set, HTTP routes require `X-API-Key` header |
| `CORS_ORIGINS` | Comma-separated allowed origins (`*` default) |
| `GROQ_MODEL` | LLM model (default `llama-3.3-70b-versatile`) |
| `GROQ_STT_MODEL` | Whisper model (default `whisper-large-v3`) |
| `REDIS_URL` | Optional; enables Redis-backed session memory |
| `APP_MAP` | JSON map of friendly app name -> Windows command/path |

## API

### REST
- `POST /api/chat` — SSE stream of reply tokens. Body: `{"session_id": "abc", "message": "..."}`
- `POST /api/stt` — multipart audio file -> `{"text": "..."}`
- `POST /api/tts` — `{"text": "...", "lang": "en"}` -> MP3 audio

### WebSocket `/ws/chat`

Client -> Server:
```json
{"type": "text",  "session_id": "abc", "text": "hello jarvis"}
{"type": "audio", "session_id": "abc", "filename": "audio.webm", "data": "<base64>"}
```

Server -> Client:
```json
{"type": "transcript", "text": "..."}     // audio input only
{"type": "token", "text": "..."}          // streamed reply
{"type": "audio", "data": "<base64 mp3>"} // spoken reply
{"type": "done"}
{"type": "error", "message": "..."}
```

## Docker

```bash
docker build -t jarvis-backend .
docker run -p 8000:8000 --env-file .env jarvis-backend
```

## Tests

```bash
pip install pytest pytest-asyncio
pytest
```

Tools are unit-tested with mocked providers; the agent smoke test skips when API keys are absent.

## Notes
- App control is **launch-only** and **whitelist-based** (see `APP_MAP`) for safety.
- Session memory is in-memory by default; set `REDIS_URL` for multi-worker deployments.
- Frontend lives in the sibling `frontend/` folder and is out of scope here.


 python -m uvicorn app.main:app --host 0.0.0.0 --port 8000"