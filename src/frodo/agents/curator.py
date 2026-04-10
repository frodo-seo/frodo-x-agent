"""Curator agent — selects the most consequential stories from a headline pool."""

from ..llm import LLMClient
from ._json_utils import parse_json_loose

_CURATOR_SYSTEM = (
    "너는 한국 독자를 위한 미국 뉴스 큐레이터다. "
    "지시받은 JSON 형식으로만 출력한다. 다른 텍스트는 절대 쓰지 않는다."
)


def _format_headlines(headlines: list[dict]) -> str:
    chunks = []
    for i, r in enumerate(headlines, 1):
        title = (r.get("title") or "").strip()
        content = (r.get("content") or "").strip()[:300]
        url = r.get("url", "")
        chunks.append(f"[{i}] {title}\n{content}\n출처: {url}")
    return "\n\n".join(chunks)


def select_topics(
    headlines: list[dict],
    llm: LLMClient,
    n: int = 3,
    covered_recently: list[str] | None = None,
) -> list[str]:
    if not headlines:
        return []

    avoid_block = ""
    if covered_recently:
        topics_list = "\n".join(f"- {t}" for t in covered_recently)
        avoid_block = f"""
== 최근 {len(covered_recently)}일 내 이미 다룬 토픽 (선택 금지) ==
{topics_list}

같은 이슈를 오늘도 선택하지 마라. 완전히 새로운 전개나 새로운 각도가 있어야만 예외적으로 허용.
"""

    prompt = f"""오늘 미국 주요 매체에서 수집한 헤드라인이다.

{_format_headlines(headlines)}
{avoid_block}
이 중에서 **한국 독자가 아침에 알아야 할 가장 중요한 뉴스 {n}개**를 골라라.

선정 기준:
- 한국에 영향이 있는 것 우선 (반도체, 자동차, 동맹, 환율, 북한, 중국, 무역, 에너지)
- 정치 가십이 아닌 실질적 사건 또는 정책
- 같은 사건의 중복 보도는 하나로 묶기

출력: JSON 배열만. 다른 텍스트 금지.
각 원소는 그 뉴스를 더 깊이 검색하기 좋은 짧은 영어 쿼리(8단어 이내).

예시:
["Trump tariffs on EU autos", "Fed rate decision delayed", "China rare earth export controls"]"""

    raw = llm.generate(_CURATOR_SYSTEM, prompt)
    parsed = parse_json_loose(raw)
    if isinstance(parsed, list):
        return [str(t) for t in parsed][:n]
    return []
