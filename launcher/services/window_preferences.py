from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path


class CloseAction(StrEnum):
    ASK = "ask"
    MINIMIZE_TO_TRAY = "minimize_to_tray"
    EXIT = "exit"


class WindowPreferenceStore:
    def __init__(self, state_dir: Path) -> None:
        self.state_dir = state_dir
        self.preference_file = state_dir / "window-preferences.json"

    def load_close_action(self) -> CloseAction:
        payload = self._load_payload()
        raw_action = str(payload.get("closeAction") or CloseAction.ASK)
        try:
            return CloseAction(raw_action)
        except ValueError:
            return CloseAction.ASK

    def save_close_action(self, action: CloseAction) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        payload = self._load_payload()
        payload["closeAction"] = action.value
        self.preference_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_payload(self) -> dict[str, object]:
        if not self.preference_file.exists():
            return {}
        try:
            payload = json.loads(self.preference_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(payload, dict):
            return {}
        return payload
