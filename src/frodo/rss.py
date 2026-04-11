"""Google News RSS fetcher — no auth, no API key required.

Used as the primary discovery layer (what's trending in US news right now).
Tavily is reserved for deep-diving into specific topics after Curator picks them.
"""

import re

import feedparser

# Google News public RSS feeds, US edition.
# These refresh roughly every 15 minutes.
FEEDS = {
    "top":        "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "politics":   "https://news.google.com/rss/headlines/section/topic/POLITICS?hl=en-US&gl=US&ceid=US:en",
    "business":   "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "world":      "https://news.google.com/rss/headlines/section/topic/WORLD?hl=en-US&gl=US&ceid=US:en",
    "technology": "https://news.google.com/rss/headlines/section/topic/TECHNOLOGY?hl=en-US&gl=US&ceid=US:en",
}

_HTML_TAG = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG.sub(" ", text).strip()


def fetch_headlines(
    categories: list[str] | None = None,
    max_per_feed: int = 10,
) -> list[dict]:
    """Fetch and deduplicate headlines from Google News RSS.

    Args:
        categories: keys from FEEDS to fetch (default: all five).
        max_per_feed: max entries to take from each feed.

    Returns:
        List of dicts with keys: title, url, content, source.
        Compatible with the shape Tavily returns so existing Curator code
        works without changes.
    """
    urls = [FEEDS[c] for c in (categories or FEEDS.keys()) if c in FEEDS]

    seen: set[str] = set()
    results: list[dict] = []

    failed_feeds: list[str] = []

    for url in urls:
        try:
            feed = feedparser.parse(url)
        except Exception:
            failed_feeds.append(url)
            continue

        if feed.bozo and not feed.entries:
            failed_feeds.append(url)
            continue

        feed_name = feed.feed.get("title", "Google News")

        for entry in feed.entries[:max_per_feed]:
            title = entry.get("title", "").strip()
            if not title or title in seen:
                continue
            seen.add(title)

            summary = _strip_html(entry.get("summary", ""))

            results.append(
                {
                    "title": title,
                    "url": entry.get("link", ""),
                    "content": summary or title,
                    "source": feed_name,
                }
            )

    if failed_feeds:
        print(f"  [warn] RSS 피드 {len(failed_feeds)}/{len(urls)}개 실패: {failed_feeds}")
    if not results:
        print("  [error] 모든 RSS 피드에서 헤드라인을 가져오지 못함")

    return results
