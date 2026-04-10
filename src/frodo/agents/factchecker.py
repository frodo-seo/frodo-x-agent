"""Fact-checker agent — final gate before posting.

Two-step process:
  1. LLM extracts the 2-3 most specific, verifiable claims from the draft.
  2. Tavily searches each claim independently.
  3. LLM verdicts whether each claim is supported, unverified, or contradicted.

If any claim is contradicted → passed=False → pipeline skips posting.
Unverified claims (search found nothing) are flagged but don't block by default.
"""

from ..llm import LLMClient
from ..models import FactCheckResult
from ..search import NagneSearch
from ._json_utils import parse_json_loose

_EXTRACTOR_SYSTEM = (
    "너는 팩트체커다. 텍스트에서 검증 가능한 구체적 주장만 추출한다. "
    "JSON만 출력한다. 다른 텍스트 금지."
)

_VERDICT_SYSTEM = (
    "너는 팩트체커다. 검색 결과를 바탕으로 주장의 사실 여부를 판단한다. "
    "JSON만 출력한다. 다른 텍스트 금지."
)


def _extract_claims(text: str, llm: LLMClient) -> list[str]:
    """Extract specific verifiable claims from the draft."""
    prompt = f"""다음 X 포스트에서 팩트체크가 필요한 구체적 주장 2~3개를 추출하라.

포스트:
{text}

기준:
- 숫자, 날짜, 인명, 기관명, 사건이 포함된 구체적 주장만.
- "~할 것 같다", "~로 보인다" 같은 의견/예측은 제외.
- 검색으로 검증 가능한 것만.

출력: JSON 배열. 각 원소는 영어 검색 쿼리 (8단어 이내).
예시: ["Powell Bessent warn bank CEOs AI risk", "Fed rate hold April 2026"]"""

    raw = llm.generate(_EXTRACTOR_SYSTEM, prompt)
    parsed = parse_json_loose(raw)
    if isinstance(parsed, list):
        return [str(c) for c in parsed if c][:3]
    return []


def _verify_claim(claim: str, search: NagneSearch, llm: LLMClient) -> str:
    """Verify a single claim. Returns 'verified', 'unverified', or 'contradicted'."""
    results = search.search_any(claim, max_results=4)

    if not results:
        return "unverified"

    snippets = "\n\n".join(
        f"[{i+1}] {r.get('title','')}\n{(r.get('content') or '')[:400]}"
        for i, r in enumerate(results)
    )

    prompt = f"""주장: "{claim}"

검색 결과:
{snippets}

이 검색 결과를 기반으로 위 주장이 사실인지 판단하라.

JSON 출력:
{{
  "verdict": "verified" | "unverified" | "contradicted",
  "reason": "한 문장 이유"
}}

- verified: 검색 결과가 주장을 직접 뒷받침함
- unverified: 관련 결과가 없거나 확인 불가
- contradicted: 검색 결과가 주장과 명백히 다르거나 반박함"""

    raw = llm.generate(_VERDICT_SYSTEM, prompt)
    data = parse_json_loose(raw)
    if isinstance(data, dict):
        return str(data.get("verdict", "unverified"))
    return "unverified"


def fact_check(text: str, search: NagneSearch, llm: LLMClient) -> FactCheckResult:
    """Run full fact-check on a draft. Returns FactCheckResult."""
    claims = _extract_claims(text, llm)

    if not claims:
        # No specific verifiable claims found — pass through.
        return FactCheckResult(passed=True)

    verified, unverified, contradicted = [], [], []

    for claim in claims:
        verdict = _verify_claim(claim, search, llm)
        if verdict == "verified":
            verified.append(claim)
        elif verdict == "contradicted":
            contradicted.append(claim)
        else:
            unverified.append(claim)

    passed = len(contradicted) == 0

    return FactCheckResult(
        passed=passed,
        verified=verified,
        unverified=unverified,
        contradicted=contradicted,
    )
