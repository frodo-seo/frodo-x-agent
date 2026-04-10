from google import genai
from google.genai import types


class LLMClient:
    """Wrapper around Google AI Studio (Gemini API).

    Uses the model's native system_instruction so the persona prompt
    stays cleanly separated from user content.
    """

    def __init__(self, api_key: str, model: str):
        self.client = genai.Client(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.models.generate_content(
            model=self.model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
            ),
        )
        return (response.text or "").strip()
