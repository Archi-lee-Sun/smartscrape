import feedparser
from datetime import datetime, timezone
from typing import List
from ..models import RawItem

RSS_FEED_URLS = [
    "https://faroutmagazine.co.uk/feed/",
    "https://americansongwriter.com/feed/",
    "https://www.worldhistory.org/rss2/?lang=en",
    "https://greekreporter.com/feed/",
    "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "https://www.transfermarkt.co.uk/rss/news",
    "https://www.coachesvoice.com/feed/",
    "https://spielverlagerung.com/feed/",
    "https://holdingmidfield.com/feed/",
]

def fetch_rss_feed(url : str) -> List[RawItem] :
    feed = feedparser.parse(url)

    if not feed.entries :
        print(f"Error or empty feed for URL: {url}")
        return []
    
    source_name = feed.feed.get('title' , 'Unknown Source')

    parsed_items = []

    for entry in feed.entries :
        title = entry.get('title' , 'No Title')
        content = entry.get('summary' , entry.get('description' , 'No Content'))
        url_link = entry.get('link' , None)
        published_parsed = entry.get('published_parsed' , None)

        if published_parsed :
            try :
                published_at = datetime(*published_parsed[:6], tzinfo=timezone.utc)
            except Exception :
                published_at = datetime.now(timezone.utc)
        else :
            published_at = datetime.now(timezone.utc)

        fetched_at = datetime.now(timezone.utc)

        if not url_link :
            continue

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
    for url in RSS_FEED_URLS:
        items = fetch_rss_feed(url)
        print(f"{url} -> {len(items)} items")