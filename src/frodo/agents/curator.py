"""Curator agent — selects the most consequential stories from a headline pool."""

from ..llm import LLMClient
from ._json_utils import parse_json_loose

_CURATOR_SYSTEM = (
    "너는 한국 독자를 위한 미국 뉴스 큐레이터다. "
    "출력은 반드시 JSON 문자열 배열이다. 객체 배열이 아니라 문자열 배열이다. "
    "예시: [\"Trump tariffs EU\", \"Fed rate hold\"]. "
    "다른 텍스트, 설명, 객체는 절대 쓰지 않는다."
)


def _format_headlines(headlines: list[dict]) -> str:
    chunks = []
    for i, r in enumerate(headlines, 1):
        title = (r.get("title") or "").strip()
        source = r.get("source", "")
        chunks.append(f"[{i}] {title} ({source})")
    return "\n".join(chunks)


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

    prompt = f"""오늘 Google News에서 수집한 미국 뉴스 헤드라인이다 (제목만 있음, 본문 없음).

{_format_headlines(headlines)}
{avoid_block}
이 중에서 **한국 20~30대가 아침에 보면 흥미로울 뉴스 {n}개**를 골라라.

선정 기준 (우선순위 순):
1. "와 이거 ㅋㅋ" 반응이 나올 만한 임팩트 있는 뉴스
2. 글로벌 경제, 지정학, 테크, 에너지, 무역 등 실질적 사건
3. 한국 연결고리가 있으면 가산점이지만 필수는 아님
4. 같은 사건의 중복 보도는 하나로 묶기

제외 (절대 선택 금지):
- 미국 정치인 개인 스캔들/성비위/이혼/소송 등 가십
- 미국 로컬 사건 (총기, 범죄, 사고, 주(州) 단위 정치)
- 연예, 스포츠
- 한국 20~30대가 "그래서?" 할 만한 임팩트 없는 뉴스

출력: **JSON 문자열 배열만.** 객체({{}}) 절대 금지. 설명, headline, summary 필드 금지.
각 원소는 짧은 영어 검색 쿼리(8단어 이내)이고, 문자열이다.

정확한 출력 형식:
["Trump tariffs on EU autos", "Fed rate decision delayed", "China rare earth export controls"]"""

    raw = llm.generate(_CURATOR_SYSTEM, prompt)
    parsed = parse_json_loose(raw)
    if not isinstance(parsed, list):
        return []

    topics: list[str] = []
    for item in parsed:
        if isinstance(item, str):
            topics.append(item)
        elif isinstance(item, dict):
            # Claude sometimes returns structured objects instead of plain strings.
            # Extract the search query, falling back to headline or first string value.
            query = item.get("query") or item.get("search_query") or item.get("headline") or ""
            if query:
                topics.append(str(query))
    return topics[:n]
