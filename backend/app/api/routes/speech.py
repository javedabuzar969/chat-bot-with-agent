import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import Response

from app.api.deps import require_api_key
from app.core.stt import transcribe_audio
from app.core.tts import synthesize_speech
from app.schemas import TTSRequest, TranscriptResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["speech"])


@router.post("/stt", response_model=TranscriptResponse)
async def speech_to_text(
    file: UploadFile = File(...), _: None = Depends(require_api_key)
):
    """Transcribe an uploaded audio file to text using Groq Whisper."""
    try:
        audio = await file.read()
        text = await transcribe_audio(audio, file.filename or "audio.webm")
        return TranscriptResponse(text=text)
    except Exception as exc:  # noqa: BLE001
        logger.exception("STT failed")
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/tts")
async def text_to_speech(req: TTSRequest, _: None = Depends(require_api_key)):
    """Convert text to spoken MP3 audio using gTTS."""
    audio = synthesize_speech(req.text, req.lang)
    if not audio:
        raise HTTPException(status_code=400, detail="Empty text.")
    return Response(content=audio, media_type="audio/mpeg")
