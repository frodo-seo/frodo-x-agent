"""Dedup agent — checks whether a new post overlaps with already-accepted posts."""

from ..llm import LLMClient

_DEDUP_SYSTEM = (
    "너는 뉴스 중복 판별기다. "
    "두 포스트가 같은 사건·이슈를 다루는지 판단한다. "
    "출력은 반드시 YES 또는 NO 한 단어만."
)


def is_duplicate(
    new_text: str,
    accepted_texts: list[str],
    llm: LLMClient,
) -> bool:
    """Return True if new_text covers the same story as any accepted post."""
    if not accepted_texts:
        return False

    existing_block = "\n---\n".join(
        f"[포스트 {i + 1}]\n{t}" for i, t in enumerate(accepted_texts)
    )

    prompt = f"""아래는 이미 게시 확정된 포스트들이다:

{existing_block}

---

아래는 새로 작성된 포스트다:

{new_text}

새 포스트가 기존 포스트 중 하나와 **같은 사건이나 이슈**를 다루고 있으면 YES, 아니면 NO.
앵글이 달라도 핵심 사건이 같으면 YES다."""

    raw = llm.generate(_DEDUP_SYSTEM, prompt).strip().upper()
    return raw.startswith("YES")
