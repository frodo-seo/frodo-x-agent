"""Pipeline orchestrator — runs the agent pipeline end to end.

Flow per topic:
    Tavily search → Researcher → Writer → (Validator + Editor) → revise loop
"""

from .agents import extract_brief, fact_check, review_post, select_topics, write_post
from .llm import LLMClient
from .models import PostResult
from . import post_log
from .search import NagneSearch
from .validators import find_issues

MAX_REVISIONS = 2


def draft_one(topic: str, search: NagneSearch, llm: LLMClient) -> PostResult:
    """Run the full agent pipeline for a single topic."""
    results = search.search_topic(topic)
    brief = extract_brief(topic, results, llm)

    if brief is None:
        return PostResult(
            topic=topic,
            brief=None,
            text="",
            revisions=0,
            final_issues=["브리프 추출 실패 (검색 결과 없음 또는 JSON 파싱 실패)"],
        )

    feedback: list[str] = []
    text = ""

    for attempt in range(MAX_REVISIONS + 1):
        text = write_post(brief, llm, feedback=feedback or None)

        # Append source URL before validation so character budget is accurate.
        # X shortens all URLs to 23 chars (t.co), so the cost is fixed.
        full_text = f"{text}\n{brief.source_url}" if brief.source_url else text

        det_issues = find_issues(full_text)
        review = review_post(text, brief, llm)
        llm_issues = review.issues if not review.passed else []

        all_issues = det_issues + llm_issues

        if not all_issues:
            # Final gate: fact-check before accepting the post.
            fc = fact_check(full_text, search, llm)
            if not fc.passed:
                fc_issues = [f"팩트체크 실패 — 반박된 주장: {c}" for c in fc.contradicted]
                return PostResult(
                    topic=topic,
                    brief=brief,
                    text=full_text,
                    revisions=attempt,
                    final_issues=fc_issues,
                )
            if fc.unverified:
                # Unverified claims are logged but don't block posting.
                print(f"  [factcheck] 검증 불가 주장 (포스팅은 진행): {fc.unverified}")

            post_log.save(topic, brief.headline, full_text)
            return PostResult(
                topic=topic,
                brief=brief,
                text=full_text,
                revisions=attempt,
                final_issues=[],
            )

        if attempt == MAX_REVISIONS:
            return PostResult(
                topic=topic,
                brief=brief,
                text=full_text,
                revisions=attempt,
                final_issues=all_issues,
            )

        # Feed back text-only issues to Writer (URL isn't its concern).
        feedback = det_issues + review.suggestions

    return PostResult(
        topic=topic, brief=brief, text=text, revisions=MAX_REVISIONS, final_issues=[]
    )


def draft_brief(
    search: NagneSearch, llm: LLMClient, n: int = 3
) -> list[PostResult]:
    """Discover top stories of the day and run the pipeline on each."""
    headlines = search.discover_headlines()
    covered = post_log.recent_topics()
    topics = select_topics(headlines, llm, n=n, covered_recently=covered)
    return [draft_one(topic, search, llm) for topic in topics]
