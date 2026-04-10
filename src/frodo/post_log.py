"""Simple append-only post log in JSON Lines format.

Each line is one post:
{"date": "2026-04-10", "topic": "...", "headline": "...", "text": "...", "posted": false}

Kept as a flat file (posts_log.jsonl at project root) so it's easy to read,
grep, and version-control if needed.
"""

import json
from datetime import date, timedelta
from pathlib import Path

LOG_FILE = Path("posts_log.jsonl")
DEFAULT_DEDUP_DAYS = 5


def load_recent(days: int = DEFAULT_DEDUP_DAYS) -> list[dict]:
    """Return log entries from the last `days` days."""
    if not LOG_FILE.exists():
        return []
    cutoff = date.today() - timedelta(days=days)
    entries: list[dict] = []
    with LOG_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entry = json.loads(line)
                if date.fromisoformat(entry["date"]) >= cutoff:
                    entries.append(entry)
            except (json.JSONDecodeError, KeyError, ValueError):
                continue
    return entries


def recent_topics(days: int = DEFAULT_DEDUP_DAYS) -> list[str]:
    """Return the list of topics already covered in the last `days` days."""
    return [e["topic"] for e in load_recent(days) if e.get("topic")]


def save(topic: str, headline: str, text: str, posted: bool = False) -> None:
    entry = {
        "date": date.today().isoformat(),
        "topic": topic,
        "headline": headline,
        "text": text,
        "posted": posted,
    }
    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
