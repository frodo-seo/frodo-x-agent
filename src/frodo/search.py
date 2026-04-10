from tavily import TavilyClient

from .rss import fetch_headlines

# Slightly conservative-leaning US outlets, with a couple of neutral wires
# (Reuters, Bloomberg) and centrist DC coverage (The Hill) for balance.
US_DOMAINS = [
    "wsj.com",
    "nypost.com",
    "foxnews.com",
    "foxbusiness.com",
    "nationalreview.com",
    "thefp.com",
    "thedispatch.com",
    "washingtonexaminer.com",
    "washingtontimes.com",
    "realclearpolitics.com",
    "bloomberg.com",
    "reuters.com",
    "thehill.com",
]


class NagneSearch:
    """Tavily wrapper biased toward US (mostly center-right) outlets."""

    def __init__(self, api_key: str):
        self.client = TavilyClient(api_key=api_key)

    def search_topic(self, query: str, max_results: int = 6) -> list[dict]:
        """Deep search on a specific topic, restricted to our US source list."""
        result = self.client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_domains=US_DOMAINS,
        )
        return result.get("results", [])

    def search_any(self, query: str, max_results: int = 4) -> list[dict]:
        """Unrestricted global search — used by fact-checker to verify claims
        against any credible source, not just our US domain list.
        Uses basic depth (1 credit) since we only need existence confirmation."""
        result = self.client.search(
            query=query,
            search_depth="basic",
            max_results=max_results,
        )
        return result.get("results", [])

    def discover_headlines(self, max_per_feed: int = 10) -> list[dict]:
        """Fetch today's top US headlines via Google News RSS.

        Google News aggregates hundreds of sources and refreshes every ~15 min,
        giving us a real-time editorial signal with zero API credits spent.
        Tavily is reserved for deep-diving into the topics Curator selects.
        """
        return fetch_headlines(max_per_feed=max_per_feed)
