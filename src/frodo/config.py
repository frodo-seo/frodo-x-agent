import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str
    tavily_api_key: str
    x_api_key: str | None
    x_api_secret: str | None
    x_access_token: str | None
    x_access_token_secret: str | None
    model_id: str

    @classmethod
    def from_env(cls) -> "Config":
        def required(key: str) -> str:
            value = os.getenv(key)
            if not value:
                raise RuntimeError(f"Missing required env var: {key}")
            return value

        return cls(
            anthropic_api_key=required("ANTHROPIC_API_KEY"),
            tavily_api_key=required("TAVILY_API_KEY"),
            x_api_key=os.getenv("X_API_KEY"),
            x_api_secret=os.getenv("X_API_SECRET"),
            x_access_token=os.getenv("X_ACCESS_TOKEN"),
            x_access_token_secret=os.getenv("X_ACCESS_TOKEN_SECRET"),
            model_id=os.getenv("MODEL_ID") or "claude-sonnet-4-6",
        )

    def can_post_to_x(self) -> bool:
        return all(
            [
                self.x_api_key,
                self.x_api_secret,
                self.x_access_token,
                self.x_access_token_secret,
            ]
        )
