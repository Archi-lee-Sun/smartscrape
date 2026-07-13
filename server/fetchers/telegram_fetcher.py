from telethon import TelegramClient
from datetime import datetime, timezone
from typing import List
from ..models import RawItem
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncio

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

TELEGRAM_CHANNEL_USERNAMES = [
    "FabrizioRomanoTG",
    "FootballHistor",
    "ClassicRockNews",
    "OasisProtocolFoundation",
    "OasisProtocolCommunity",
]

api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient("smartscrape_session", api_id, api_hash)

async def fetch_telegram_channel(channel_username: str , limit: int = 20) -> List[RawItem] :
    items = []
    async with client :
        async for message in client.iter_messages(channel_username , limit=limit) :
            if not message.text :
                continue
            source_name = channel_username
            first_line = message.text.split("\n")[0]
            title = first_line[:80] + ("..." if len(first_line) > 80 else "")
            if not title :
                title = "No Title"

            content = message.text 
            url_link = f"https://t.me/{channel_username}/{message.id}"
            published_at = message.date.astimezone(timezone.utc)
            fetched_at = datetime.now(timezone.utc)

            try :
                item = RawItem(
                    source_type = "telegram",
                    source_name = source_name ,
                    title = title ,
                    content = content ,
                    url = url_link , 
                    published_at = published_at ,
                    fetched_at = fetched_at
                )
                items.append(item)
            except Exception as e :
                print(f"Error creating RawItem for message ID: {message.id}. Error: {e}")
                continue
        return items
    

if __name__ == "__main__":
    async def test():
        for channel in TELEGRAM_CHANNEL_USERNAMES:
            try:
                items = await fetch_telegram_channel(channel, limit=3)
                print(f"\n{channel} -> {len(items)} items")
                for item in items:
                    print(f"  - {item.title}")
            except Exception as e:
                print(f"{channel} -> FAILED: {e}")
    
    asyncio.run(test())
