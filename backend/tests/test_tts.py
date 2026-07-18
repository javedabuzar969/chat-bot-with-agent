from app.core.tts import synthesize_speech


def test_tts_returns_mp3_bytes():
    audio = synthesize_speech("Hello, I am Jarvis.")
    assert isinstance(audio, bytes)
    assert len(audio) > 0
    # MP3 frames start with an ID3 tag or 0xFF sync; gTTS emits ID3.
    assert audio[:3] == b"ID3" or audio[0] == 0xFF


def test_tts_empty():
    assert synthesize_speech("   ") == b""
