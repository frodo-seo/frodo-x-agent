"""Editor agent — LLM-side review of a draft against the brief and persona.

Pairs with `validators.find_issues` (deterministic checks). The editor
catches things regex can't: hedging tone, weak Korean linkage, factual
drift from the brief, missing source citation.
"""

from ..llm import LLMClient
from ..models import EditorReview, NewsBrief
from ._json_utils import parse_json_loose

_EDITOR_SYSTEM = (
    "너는 Nagne 페르소나의 편집자다. 작성된 트윗이 페르소나와 사실 정합성에 맞는지 검토한다. "
    "지시받은 JSON 형식으로만 출력한다."
)


def review_post(post: str, brief: NewsBrief, llm: LLMClient) -> EditorReview:
    prompt = f"""다음은 작성된 X 포스트와 그 근거가 된 브리프다.

== 브리프 ==
헤드라인: {brief.headline}
핵심 사실: {brief.key_facts}
출처 매체: {brief.outlets}
한국 연결고리: {brief.korean_angle}

== 작성된 포스트 ==
{post}

검토 항목:
1. 톤: Nagne는 "가볍고 약간 도발적, 단정적, 반말, 똑똑한 친구가 던지는 한 마디" 톤이다. 너무 점잖거나 통신사 같은가?
2. hedge 표현: "~일 수도", "~로 보인다", "~할 가능성", "~하는 듯" 같은 약한 표현이 있는가?
3. 한국 연결고리: 본문에 한국과의 연결이 명시적으로 드러나는가? (반도체/자동차/동맹/환율/북한/중국/무역/에너지)
4. 사실 정합성: 포스트의 모든 사실/숫자/인명이 브리프에서 검증되는가? 환각이 있는가?
5. 출처 인용: 매체명이 본문에 자연스럽게 한 번 이상 인용되었는가?

JSON만 출력:
{{
  "passed": true,
  "issues": [],
  "suggestions": []
}}

문제 있으면 passed: false, issues에 발견된 문제, suggestions에 구체적 수정 방향."""

    raw = llm.generate(_EDITOR_SYSTEM, prompt)
    data = parse_json_loose(raw)

    if not isinstance(data, dict):
        # If editor's output is unparseable, don't block the post.
        return EditorReview(passed=True)

    return EditorReview(
        passed=bool(data.get("passed", False)),
        issues=[str(i) for i in data.get("issues", []) if i],
        suggestions=[str(s) for s in data.get("suggestions", []) if s],
    )
