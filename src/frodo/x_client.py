import tweepy

from .validators import X_MAX_WEIGHTED, x_weighted_length


class XClient:
    def __init__(
        self,
        api_key: str,
        api_secret: str,
        access_token: str,
        access_token_secret: str,
    ):
        self.client = tweepy.Client(
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_token_secret,
        )

    def post(self, text: str) -> str:
        weighted = x_weighted_length(text)
        if weighted > X_MAX_WEIGHTED:
            raise ValueError(
                f"Tweet exceeds {X_MAX_WEIGHTED} weighted chars: {weighted}"
            )
        response = self.client.create_tweet(text=text)
        return response.data["id"]
