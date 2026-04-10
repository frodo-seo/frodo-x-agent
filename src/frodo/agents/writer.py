"""Writer agent — turns a NewsBrief into a Nagne-voiced X post."""

from ..llm import LLMClient
from ..models import NewsBrief
from ..persona import NAGNE_SYSTEM_PROMPT


def write_post(
    brief: NewsBrief,
    llm: LLMClient,
    feedback: list[str] | None = None,
) -> str:
    feedback_block = ""
    if feedback:
        joined = "\n".join(f"- {f}" for f in feedback)
        feedback_block = (
            "\n\n== 이전 시도에서 발견된 문제 (반드시 모두 해결할 것) ==\n"
            f"{joined}\n"
        )

    prompt = f"""아래 브리프를 바탕으로 Nagne 페르소나로 X 포스트 1개를 작성하라.

== 브리프 ==
헤드라인: {brief.headline}

핵심 사실:
{chr(10).join(f"- {f}" for f in brief.key_facts)}

출처 매체: {", ".join(brief.outlets) if brief.outlets else "(미상)"}

한국 연결고리: {brief.korean_angle}
{feedback_block}
출력 규칙 (모두 준수):
- **한국어 글자 수를 직접 세어라. 반드시 100자 이하.** 포스트 끝에 URL이 자동으로 붙으므로 텍스트 자체는 짧아야 한다. 100자 초과하면 무조건 탈락이다.
- 문장은 2~3개로 제한. 길게 쓰지 마라.
- 본문만 출력. 따옴표, "초안:", 설명 등 메타 텍스트 금지.
- 이모지 0개. 해시태그 0개.
- 단정 평서문으로 끝낸다. "~아냐?", "~아닐까?" 금지.
- 브리프에 없는 사실은 절대 추가하지 마라.
- 출처 매체 1개 이상을 본문에 자연스럽게 인용한다."""

    return llm.generate(NAGNE_SYSTEM_PROMPT, prompt).strip()
