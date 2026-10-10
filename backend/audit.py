"""Append-only audit trail at output/audit_trail.json (a JSON list of entries)."""

import json
import os
import threading
from datetime import datetime, timezone
from typing import Any

from backend.config import AUDIT_TRAIL

MAX_FIELD_CHARS = 300
_lock = threading.Lock()


def short(value: Any) -> str:
    """Compact one-line text, cut to MAX_FIELD_CHARS."""
    text = value if isinstance(value, str) else json.dumps(value, default=str, separators=(",", ":"))
    text = " ".join(text.split())
    return text if len(text) <= MAX_FIELD_CHARS else text[: MAX_FIELD_CHARS - 3] + "..."


def append(entry: dict) -> None:
    """Add one entry to the trail. Existing entries are never removed.

    If the file exists but isn't a JSON list, raise instead of overwriting it.
    """
    entry = {"time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), **entry}
    with _lock:
        AUDIT_TRAIL.parent.mkdir(parents=True, exist_ok=True)
        entries: list = []
        if AUDIT_TRAIL.exists() and AUDIT_TRAIL.stat().st_size > 0:
            entries = json.loads(AUDIT_TRAIL.read_text())
            if not isinstance(entries, list):
                raise RuntimeError(f"{AUDIT_TRAIL} is not a JSON list; refusing to overwrite it.")
        entries.append(entry)
        tmp = AUDIT_TRAIL.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(entries, indent=2))
        os.replace(tmp, AUDIT_TRAIL)
