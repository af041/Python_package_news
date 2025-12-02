from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

from .models import StateEntry


def load_state(path: str | Path) -> Dict[str, StateEntry]:
    state_path = Path(path)
    if not state_path.exists():
        return {}
    data = json.loads(state_path.read_text(encoding="utf-8")) or {}
    packages = data.get("packages", {})
    result: Dict[str, StateEntry] = {}
    for pkg, entry in packages.items():
        try:
            result[pkg] = StateEntry(
                last_seen_version=entry["last_seen_version"],
                last_checked_at=datetime.fromisoformat(entry["last_checked_at"]),
            )
        except (KeyError, ValueError):
            continue
    return result


def save_state(path: str | Path, state: Dict[str, StateEntry]) -> None:
    state_path = Path(path)
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "packages": {
            name: {
                "last_seen_version": entry.last_seen_version,
                "last_checked_at": entry.last_checked_at.astimezone(timezone.utc).isoformat(),
            }
            for name, entry in state.items()
        }
    }
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def update_state(state: Dict[str, StateEntry], package: str, latest_version: str) -> None:
    state[package] = StateEntry(
        last_seen_version=latest_version,
        last_checked_at=datetime.now(timezone.utc),
    )
