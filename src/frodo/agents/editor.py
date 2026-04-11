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

검토 항목을 **hard issue**(반드시 수정)와 **soft issue**(권장 수정)로 구분하라.

hard issue (하나라도 있으면 passed: false):
- 명백한 환각: 브리프에 없는 사실/숫자/인명을 만들어낸 경우만. "공습 vs 군사작전" 같은 표현 차이나 시제 차이는 환각이 아니다.
- 출처 인용: 매체명이 본문에 한 번도 인용되지 않았는가?
- hedge 표현: "~일 수도", "~로 보인다", "~할 가능성" 같은 약한 표현이 있는가?

soft issue (있어도 passed: true, suggestions에만 기록):
- 톤이 약간 점잖거나 통신사 톤에 가까움
- 브리프 표현과 미세한 뉘앙스 차이 (차단 사유 아님)
- 한국 연결고리가 자연스럽게 들어갈 수 있는데 빠져 있음

JSON만 출력:
{{
  "passed": true,
  "issues": [],
  "suggestions": []
}}

hard issue가 있으면 passed: false + issues에 기록. soft issue만 있으면 passed: true + suggestions에 기록."""

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
