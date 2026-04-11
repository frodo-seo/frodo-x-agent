"""Researcher agent — turns raw search results into a structured NewsBrief."""

from ..llm import LLMClient
from ..models import NewsBrief
from ._json_utils import parse_json_loose

_RESEARCHER_SYSTEM = (
    "너는 뉴스 분석가다. 검색 결과에서 사실만 추출하고 한국과의 연결고리를 식별한다. "
    "지시받은 JSON 형식으로만 출력한다. 검색 결과에 없는 사실은 절대 만들어내지 않는다."
)


def _format_results(results: list[dict]) -> str:
    chunks = []
    for i, r in enumerate(results, 1):
        title = (r.get("title") or "").strip()
        content = (r.get("content") or "").strip()[:600]
        url = r.get("url", "")
        chunks.append(f"[{i}] {title}\n{content}\n출처: {url}")
    return "\n\n".join(chunks)


def extract_brief(
    topic: str, results: list[dict], llm: LLMClient
) -> NewsBrief | None:
    if not results:
        return None

    prompt = f"""주제: {topic}

== 검색 결과 ==
{_format_results(results)}

위 자료에서 다음을 추출하여 JSON으로 출력하라.

{{
  "headline": "한국어 한 줄 요약 (40자 이내)",
  "key_facts": [
    "구체적 사실 1 (숫자/이름/날짜 포함)",
    "사실 2",
    "사실 3"
  ],
  "outlets": ["WSJ", "Fox", "..."],
  "korean_angle": "한국과 자연스러운 연결고리가 있으면 한 문장. 없으면 빈 문자열.",
  "angle_strength": "strong | weak | none",
  "source_url": "가장 권위 있는 원본 기사 URL (검색 결과 중 하나)"
}}

규칙:
- 검색 결과에 없는 사실은 절대 추가하지 마라.
- key_facts는 2~4개. 각각 검색 결과에서 검증 가능해야 한다.
- 한국 연결고리가 명확하면 "strong", 약하면 "weak", 없으면 "none"으로.
- JSON만 출력. 다른 텍스트 금지."""

    raw = llm.generate(_RESEARCHER_SYSTEM, prompt)
    data = parse_json_loose(raw)
    if not isinstance(data, dict):
        return None

    try:
        return NewsBrief(
            headline=str(data.get("headline", "")).strip(),
            key_facts=[str(f) for f in data.get("key_facts", []) if f],
            outlets=[str(o) for o in data.get("outlets", []) if o],
            korean_angle=str(data.get("korean_angle", "")).strip(),
            angle_strength=str(data.get("angle_strength", "medium")).lower(),
            source_url=str(data["source_url"]).strip() if data.get("source_url") else None,
        )
    except (TypeError, ValueError):
        return None
