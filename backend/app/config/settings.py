import ast
import json
from functools import lru_cache
from typing import Dict, List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # General
    app_name: str = "Jarvis Backend"
    environment: str = "development"
    log_level: str = "INFO"
    cors_origins: str | List[str] = "*"

    # API security (optional). If set, HTTP routes require the X-API-Key header.
    api_key: str | None = None

    # Providers
    groq_api_key: str = ""
    tavily_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_stt_model: str = "whisper-large-v3"
    groq_chat_temperature: float = 0.3

    # Session / memory
    redis_url: str | None = None
    session_ttl_seconds: int = 60 * 60 * 24  # 1 day

    # Application launcher whitelist: friendly name -> Windows command/path
    app_map: Dict[str, str] = {
        "notepad": "notepad.exe",
        "calculator": "calc.exe",
        "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
        "edge": "msedge.exe",
        "firefox": "firefox.exe",
        "explorer": "explorer.exe",
        "cmd": "cmd.exe",
        "powershell": "powershell.exe",
        "paint": "mspaint.exe",
        "word": "winword.exe",
        "excel": "excel.exe",
        "spotify": "spotify.exe",
    }

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @field_validator("app_map", mode="before")
    @classmethod
    def parse_app_map(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                try:
                    return ast.literal_eval(v)
                except (ValueError, SyntaxError):
                    raise ValueError(
                        "APP_MAP must be valid JSON or Python dict literal"
                    )
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()
