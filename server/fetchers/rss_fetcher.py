import feedparser
from datetime import datetime, timezone
from typing import List
from ..models import RawItem
from .content_fetcher import fetch_full_article

RSS_FEED_ARTICLE_LIMITS = {
    "https://faroutmagazine.co.uk/feed/": 7,
    "https://americansongwriter.com/feed/": 4,
    "https://www.worldhistory.org/rss2/?lang=en": 4,
    "https://feeds.bbci.co.uk/sport/football/rss.xml": 7,
    "https://www.transfermarkt.co.uk/rss/news": 7,
    "https://www.coachesvoice.com/feed/": 7,
    "https://spielverlagerung.com/feed/": 7,
    "https://holdingmidfield.com/feed/": 7,
    "https://thesefootballtimes.co/feed/": 7,
    "https://feeds.acast.com/public/shows/achtung-radio": 4,
    "https://www.11v11.com/feed/": 7,
}

RSS_FEED_URLS = list(RSS_FEED_ARTICLE_LIMITS)


def fetch_rss_feed(url : str) -> List[RawItem] :
    feed = feedparser.parse(url)

    if not feed.entries :
        print(f"Error or empty feed for URL: {url}")
        return []
    
    source_name = feed.feed.get('title' , 'Unknown Source')

    parsed_items = []

    article_limit = RSS_FEED_ARTICLE_LIMITS.get(url, 4)

    for entry in feed.entries[:article_limit] :
        title = entry.get('title' , 'No Title')
        url_link = entry.get('link' , None)

        if not url_link:
            continue

        content = None

        try :
            content =   fetch_full_article(url_link)
        except Exception as e :
            print(f"Warning: Failed to fetch full article for {url_link}. Error: {e}")

        if not content or not content.strip():
            continue

        content = content.strip()

        published_parsed = entry.get('published_parsed' , None)

        if published_parsed :
            try :
                published_at = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            except Exception :
                published_at = datetime.now(timezone.utc)
        else :
            published_at = datetime.now(timezone.utc)

        fetched_at = datetime.now(timezone.utc)


        try :
            raw_item = RawItem(
                source_type = "rss",
                source_name = source_name ,
                title = title ,
                content = content ,
                url = url_link , 
                published_at = published_at , 
                fetched_at = fetched_at
            )
            parsed_items.append(raw_item)
        except Exception as e :
            print(f"Error creating RawItem for entry: {title}. Error: {e}")
            continue
        
    return parsed_items


if __name__ == "__main__":
    for url in RSS_FEED_URLS :
        items = fetch_rss_feed(url)
        print(f"{url} -> {len(items)} items")
