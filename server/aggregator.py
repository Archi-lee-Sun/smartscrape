import asyncio
from .fetchers.rss_fetcher import fetch_rss_feed, RSS_FEED_URLS
from .models import RawItem
from typing import List
from .fetchers.telegram_fetcher import fetch_telegram_channel, TELEGRAM_CHANNEL_USERNAMES

async def aggregate_all_sources() -> List[RawItem] :
    all_items = []

    for url in RSS_FEED_URLS :
        try :
            items = await asyncio.to_thread(fetch_rss_feed, url)
            all_items.extend(items)
        except Exception as e :
            print(f"Error fetching RSS_feed for url : {url} . Error: {e}")
    
    for channel in TELEGRAM_CHANNEL_USERNAMES :
        try :
            items = await fetch_telegram_channel(channel, 20)
            all_items.extend(items)
        except Exception as e :
            print(f"Error fetching Telegram channel : {channel} . Error: {e}")

    return all_items  


if __name__ == "__main__":
    items = asyncio.run(aggregate_all_sources())
    print(f"Total items fetched: {len(items)}")

    for item in items:
        print(f"[{item.source_type}] {item.source_name}: {item.title} \n {item.content}")