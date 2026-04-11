import time

import anthropic


class LLMClient:
    """Wrapper around the Anthropic API (Claude)."""

    MAX_RETRIES = 3
    RETRY_BACKOFF = (1, 3, 5)  # seconds between retries

    def __init__(self, api_key: str, model: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        last_err: Exception | None = None

        for attempt in range(self.MAX_RETRIES):
            try:
                message = self.client.messages.create(
                    model=self.model,
                    max_tokens=1024,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                )
                return message.content[0].text.strip()
            except (
                anthropic.RateLimitError,
                anthropic.InternalServerError,
                anthropic.APIConnectionError,
            ) as e:
                last_err = e
                wait = self.RETRY_BACKOFF[min(attempt, len(self.RETRY_BACKOFF) - 1)]
                print(f"  [retry] LLM 호출 실패 ({type(e).__name__}), {wait}초 후 재시도 ({attempt + 1}/{self.MAX_RETRIES})")
                time.sleep(wait)

        raise last_err  # type: ignore[misc]
