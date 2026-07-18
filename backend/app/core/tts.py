import io
import re

from gtts import gTTS


def _chunk_text(text: str, max_chars: int = 4500) -> list[str]:
    """Split long text into chunks small enough for gTTS, on sentence boundaries."""
    if len(text) <= max_chars:
        return [text]
    sentences = re.split(r"(?<=[.!?])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current)
            current = sentence
    if current:
        chunks.append(current)
    return chunks or [text]


def synthesize_speech(text: str, lang: str = "en") -> bytes:
    """Convert text to MP3 audio bytes using gTTS (free, no API key)."""
    text = (text or "").strip()
    if not text:
        return b""
    buf = io.BytesIO()
    for chunk in _chunk_text(text):
        part = io.BytesIO()
        gTTS(text=chunk, lang=lang, slow=False).write_to_fp(part)
        buf.write(part.getvalue())
    return buf.getvalue()
