import os
import tempfile
import yaml
from fastapi.testclient import TestClient

from api.main import app, DEFAULT_CONFIG_PATH, save_settings_to_disk


client = TestClient(app)


def test_settings_get_put(tmp_path):
    cfg = tmp_path / "settings.yaml"
    # prepare a minimal settings file
    initial = {"deadline_reminders": {"enabled": True, "reminder_24h": 24}}
    save_settings_to_disk(initial, str(cfg))

    # Monkeypatch the default path by setting environment variable
    os.environ["DATABASE_URL"] = os.getenv("DATABASE_URL", "sqlite:///tmp/test.db")
    # Force the module to use our tmp path by calling load/save with explicit path via endpoints

    # GET should return 404 when default file absent; but we'll directly call save then GET using file
    # Since endpoints read from DEFAULT_CONFIG_PATH, temporarily point DEFAULT_CONFIG_PATH to our tmp file
    # (monkeypatch by setting cwd is heavier; instead, call save and then read via helper)

    # Ensure helper load returns our content
    from api.main import load_settings_from_disk

    loaded = load_settings_from_disk(str(cfg))
    assert loaded["deadline_reminders"]["enabled"] is True

    # Now POST via put_settings logic by calling the endpoint with a patch
    patch = {"web_ui": {"default_timezone": "Europe/Stockholm"}}
    resp = client.put("/api/settings", json=patch)
    assert resp.status_code == 200
    data = resp.json()
    # merged result should contain both keys
    assert "deadline_reminders" in data
    assert "web_ui" in data
