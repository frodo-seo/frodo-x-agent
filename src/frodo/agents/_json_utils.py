"""Robust JSON extraction from LLM output.

LLMs love to wrap JSON in code fences or add prose around it. This tries
hard to dig out a parseable structure.
"""

import json
import re


def parse_json_loose(raw: str) -> object | None:
    """Try to extract a JSON value from arbitrary LLM output.

    Returns the parsed object, or None if nothing parseable found.
    """
    if not raw:
        return None

    cleaned = re.sub(
        r"^```(?:json)?\s*|\s*```$",
        "",
        raw.strip(),
        flags=re.MULTILINE,
    )

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass

    # Fall back: find the first {...} or [...] block
    for pattern in (r"\{.*\}", r"\[.*\]"):
        match = re.search(pattern, cleaned, flags=re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except json.JSONDecodeError:
                continue

    return None
