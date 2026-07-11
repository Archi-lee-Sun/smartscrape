from datetime import datetime, timezone
from unittest.mock import Mock, patch

from server.groq_client import extract_summary, format_articles, synthesize_cluster
from server.models import RawItem


def raw_item(
    source_name: str = "BBC Sport",
    title: str = "Test title",
    content: str = "Test content",
) -> RawItem:
    timestamp = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return RawItem(
        source_type="rss",
        source_name=source_name,
        title=title,
        content=content,
        url="https://example.com/test",
        published_at=timestamp,
        fetched_at=timestamp,
    )


def test_format_articles_unescapes_html_strips_tags_and_wraps_articles():
    group = [
        raw_item(
            title="<b>Chelsea &amp; Sporting</b>",
            content="<p>Quenda signs &amp; joins the squad.</p>",
        ),
        raw_item(
            title="History &amp; archives",
            content="<div>Late Period &amp; Third Intermediate Period.</div>",
        ),
    ]

    assert format_articles(group) == (
        '<article n="1">\n'
        "  <title>Chelsea & Sporting</title>\n"
        "  <content>Quenda signs & joins the squad.</content>\n"
        "</article>\n\n"
        '<article n="2">\n'
        "  <title>History & archives</title>\n"
        "  <content>Late Period & Third Intermediate Period.</content>\n"
        "</article>"
    )


def test_extract_summary_returns_inner_text_from_well_formed_tags():
    assert extract_summary("<summary>  Clean summary.  </summary>") == "Clean summary."


def test_extract_summary_falls_back_to_raw_text_without_tags():
    assert extract_summary("Plain raw summary.") == "Plain raw summary."


def test_extract_summary_falls_back_to_raw_text_for_empty_tags():
    assert extract_summary("<summary></summary>") == "<summary></summary>"


def test_synthesize_cluster_returns_summary_from_mocked_completion():
    fake_completion = Mock(
        choices=[Mock(message=Mock(content="<summary>Mocked summary.</summary>"))]
    )
    group = [raw_item()]

    with patch(
        "server.groq_client.client.chat.completions.create",
        return_value=fake_completion,
    ) as create:
        result = synthesize_cluster(group)

    assert result == "Mocked summary."
    create.assert_called_once()
    assert create.call_args.kwargs["model"] == "openai/gpt-oss-20b"
    assert create.call_args.kwargs["temperature"] == 0.2


def test_synthesize_cluster_returns_none_when_groq_call_raises():
    group = [raw_item()]

    with patch(
        "server.groq_client.client.chat.completions.create",
        side_effect=Exception("boom"),
    ):
        assert synthesize_cluster(group) is None
