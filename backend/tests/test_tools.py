from unittest.mock import MagicMock, patch

from app.agents.tools.app_launcher import open_application
from app.agents.tools.web_search import web_search


def test_open_application_known():
    with patch("app.agents.tools.app_launcher.os.startfile") as mock_start:
        result = open_application.invoke({"name": "notepad"})
        assert "Opened notepad" in result
        mock_start.assert_called_once_with("notepad.exe")


def test_open_application_unknown():
    result = open_application.invoke({"name": "photoshop"})
    assert "don't have" in result.lower()


def test_web_search_success():
    fake = MagicMock()
    fake.search.return_value = {
        "answer": "It is sunny.",
        "results": [{"title": "Weather", "content": "Sunny today.", "url": "http://w"}],
    }
    with patch("app.agents.tools.web_search.TavilyClient", return_value=fake):
        out = web_search.invoke({"query": "weather today"})
    assert "It is sunny." in out
    assert "Weather" in out


def test_web_search_no_key(monkeypatch):
    monkeypatch.setattr("app.agents.tools.web_search.get_settings")(
        lambda: __import__("app.config.settings", fromlist=["Settings"]).Settings(
            tavily_api_key=""
        )
    )
    out = web_search.invoke({"query": "x"})
    assert "unavailable" in out.lower()
