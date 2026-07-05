from .fetchers.rss_fetcher import fetch_rss_feed, RSS_FEED_URLS
from .models import RawItem
from typing import List

def aggregate_all_sources() -> List[RawItem] :
    all_items = []

    for url in RSS_FEED_URLS :
        try :
            items = fetch_rss_feed(url)
            all_items.extend(items)
        except Exception as e :
            print(f"Error fetching RSS_feed for url : {url} . Error: {e}")


    return all_items  


if __name__ == "__main__":
    items = aggregate_all_sources()
    print(f"Total items fetched: {len(items)}")
    for item in items[:5]:
        print(f"[{item.source_type}] {item.source_name}: {item.title}")

