from types import SimpleNamespace
from unittest.mock import patch

from server.fetchers.rss_fetcher import RSS_FEED_ARTICLE_LIMITS, fetch_rss_feed


def _feed_with(entry):
    return SimpleNamespace(entries=[entry], feed={"title": "Test feed"})


def test_fetch_rss_feed_skips_item_when_full_fetch_raises():
    entry = {
        "title": "Test story",
        "link": "https://example.com/story",
        "summary": "<p>Feed teaser &amp; useful context.</p>",
    }

    with (
        patch("server.fetchers.rss_fetcher.feedparser.parse", return_value=_feed_with(entry)),
        patch(
            "server.fetchers.rss_fetcher.fetch_full_article",
            side_effect=RuntimeError("download failed"),
        ),
    ):
        items = fetch_rss_feed("https://example.com/feed")

    assert items == []


def test_fetch_rss_feed_skips_missing_link_before_full_fetch():
    entry = {"title": "No-link story", "summary": "This item has no URL."}

    with (
        patch("server.fetchers.rss_fetcher.feedparser.parse", return_value=_feed_with(entry)),
        patch("server.fetchers.rss_fetcher.fetch_full_article") as fetch_full_article,
    ):
        items = fetch_rss_feed("https://example.com/feed")

    assert items == []
    fetch_full_article.assert_not_called()


def test_fetch_rss_feed_limits_article_download_attempts_by_url():
    feed_url = "https://faroutmagazine.co.uk/feed/"
    entries = [
        {
            "title": f"Story {index}",
            "link": f"https://example.com/story-{index}",
        }
        for index in range(10)
    ]
    feed = SimpleNamespace(entries=entries, feed={"title": "Test feed"})

    with (
        patch("server.fetchers.rss_fetcher.feedparser.parse", return_value=feed),
        patch(
            "server.fetchers.rss_fetcher.fetch_full_article",
            return_value="Full article text",
        ) as fetch_full_article,
    ):
        items = fetch_rss_feed(feed_url)

    expected_limit = RSS_FEED_ARTICLE_LIMITS[feed_url]
    assert len(items) == expected_limit
    assert fetch_full_article.call_count == expected_limit
