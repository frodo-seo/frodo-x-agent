"""Deterministic checks on a draft tweet — fast, 100% reliable.

Anything that can be caught with a regex or a counter belongs here, not in
the LLM editor. Reserve the LLM for tone, fact-grounding, and judgment.
"""

import re

# Most emoji/symbol/pictograph blocks. Not exhaustive but catches the
# common offenders (flags, arrows, hands, faces, country flags).
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001FAFF"  # symbols & pictographs (broad)
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F680-\U0001F6FF"  # transport & map
    "\U0001F1E0-\U0001F1FF"  # regional indicator (flags)
    "\u2600-\u27BF"           # misc symbols + dingbats
    "\u2300-\u23FF"           # misc technical
    "\u2B00-\u2BFF"           # arrows
    "]"
)

_BANNED_OPENERS = ("속보", "방금 들어온", "JUST IN", "BREAKING", "Breaking")

_RHETORICAL_ENDINGS = (
    "아닐까?",
    "아닐까",
    "않을까?",
    "않을까",
    "아냐?",
    "할까?",
    "일까?",
)

X_MAX_WEIGHTED = 280
X_URL_WEIGHT = 23   # X wraps every URL to t.co — fixed cost regardless of length
KO_SOFT_LIMIT_CHARS = 115  # for messaging; real check uses weighted length

_URL_PATTERN = re.compile(r"https?://\S+")


def x_weighted_length(text: str) -> int:
    """Approximate X's weighted character count.

    - URLs (http/https) are replaced with a 23-char placeholder to simulate
      t.co shortening — X charges exactly 23 chars for any URL.
    - CJK / Hangul / Kana (codepoint >= U+1100) count as 2.
    - Everything else counts as 1.
    """
    normalized = _URL_PATTERN.sub("x" * X_URL_WEIGHT, text)
    return sum(2 if c >= "\u1100" else 1 for c in normalized)


def find_issues(text: str) -> list[str]:
    """Return a list of human-readable issues. Empty list = clean draft."""
    issues: list[str] = []

    weighted = x_weighted_length(text)
    if weighted > X_MAX_WEIGHTED:
        issues.append(
            f"글자수 초과: {weighted} weighted chars (한도 {X_MAX_WEIGHTED}). "
            f"한국어 기준 약 {KO_SOFT_LIMIT_CHARS}자까지."
        )

    found_emojis = "".join(sorted(set(_EMOJI_PATTERN.findall(text))))
    if found_emojis:
        issues.append(f"이모지 포함 (제거 필요): {found_emojis}")

    stripped = text.strip()
    for opener in _BANNED_OPENERS:
        if stripped.startswith(opener):
            issues.append(f"금지된 도입부: '{opener}'")
            break

    rstripped = text.rstrip()
    for ending in _RHETORICAL_ENDINGS:
        if rstripped.endswith(ending):
            issues.append(f"수사 의문문 종결: '{ending}' — 평서문 단정으로 바꿀 것")
            break

    if "#" in text:
        issues.append("해시태그 포함 (제거 필요)")

    return issues
