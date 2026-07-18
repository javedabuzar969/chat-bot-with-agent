import io

from groq import AsyncGroq

from app.config import get_settings

_EXT_CONTENT_TYPE = {
    "webm": "audio/webm",
    "wav": "audio/wav",
    "mp3": "audio/mpeg",
    "m4a": "audio/m4a",
    "ogg": "audio/ogg",
    "flac": "audio/flac",
}


def _content_type(filename: str) -> str:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return _EXT_CONTENT_TYPE.get(ext, "application/octet-stream")


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """Transcribe raw audio bytes into text using Groq's Whisper model."""
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    client = AsyncGroq(api_key=settings.groq_api_key)
    file = (filename, io.BytesIO(audio_bytes), _content_type(filename))
    response = await client.audio.transcriptions.create(
        model=settings.groq_stt_model,
        file=file,  # type: ignore[arg-type]
        response_format="json",
    )
    return (response.text or "").strip()
