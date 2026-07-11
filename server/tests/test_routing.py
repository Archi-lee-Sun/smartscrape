from datetime import datetime, timezone

import pytest

from server.models import RawItem
from server.routing import get_mode_for_cluster


def raw_item(source_name: str) -> RawItem:
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return RawItem(
        source_type="rss",
        source_name=source_name,
        title="Test title",
        content="Test content",
        url="https://example.com/test",
        published_at=timestamp,
        fetched_at=timestamp,
    )


def test_get_mode_for_cluster_returns_short_for_short_sources():
    group = [
        raw_item("BBC Sport"),
        raw_item("Transfermarkt"),
    ]

    assert get_mode_for_cluster(group) == "short"


def test_get_mode_for_cluster_returns_story_for_story_sources():
    group = [
        raw_item("World History Encyclopedia"),
        raw_item("American Songwriter"),
    ]

    assert get_mode_for_cluster(group) == "story"


def test_get_mode_for_cluster_defaults_unmapped_source_to_story():
    group = [raw_item("Unknown Source")]

    assert get_mode_for_cluster(group) == "story"


def test_get_mode_for_cluster_raises_for_mixed_modes():
    group = [
        raw_item("BBC Sport"),
        raw_item("World History Encyclopedia"),
    ]

    with pytest.raises(ValueError):
        get_mode_for_cluster(group)


def test_get_mode_for_cluster_handles_single_item_cluster():
    group = [raw_item("BBC Sport")]

    assert get_mode_for_cluster(group) == "short"
