from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    session_id: str = Field(default="default", min_length=1)
    message: str = Field(min_length=1)


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class TTSRequest(BaseModel):
    text: str = Field(min_length=1)
    lang: str = "en"


class TranscriptResponse(BaseModel):
    text: str
