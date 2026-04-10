import tweepy


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
        if len(text) > 280:
            raise ValueError(f"Tweet exceeds 280 chars: {len(text)}")
        response = self.client.create_tweet(text=text)
        return response.data["id"]
