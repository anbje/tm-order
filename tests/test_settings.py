import os
import os
from fastapi.testclient import TestClient

import api.main as main


client = TestClient(main.app)


def test_settings_get_put(tmp_path):
    cfg = tmp_path / "settings.yaml"
    # prepare a minimal settings file
    initial = {"deadline_reminders": {"enabled": True, "reminder_24h": 24}}
    # write using the helper to ensure formatting
    main.save_settings_to_disk(initial, str(cfg))

    # Point the application to use our temporary settings path
    main.DEFAULT_CONFIG_PATH = str(cfg)

    # Ensure helper load returns our content
    loaded = main.load_settings_from_disk(str(cfg))
    assert loaded["deadline_reminders"]["enabled"] is True

    # Now PUT via the endpoint with a patch
    patch = {"web_ui": {"default_timezone": "Europe/Stockholm"}}
    resp = client.put("/api/settings", json=patch)
    assert resp.status_code == 200
    data = resp.json()
    # merged result should contain both keys
    assert "deadline_reminders" in data
    assert "web_ui" in data


def test_invalid_settings_payload(tmp_path):
    cfg = tmp_path / "settings.yaml"
    initial = {"deadline_reminders": {"enabled": True, "reminder_24h": 24}}
    main.save_settings_to_disk(initial, str(cfg))
    main.DEFAULT_CONFIG_PATH = str(cfg)

    # invalid because items_per_page must be >= 1
    bad_patch = {"web_ui": {"items_per_page": 0}}
    resp = client.put("/api/settings", json=bad_patch)
    assert resp.status_code == 400
    assert "Invalid settings payload" in resp.text
    patch = {"web_ui": {"default_timezone": "Europe/Stockholm"}}
