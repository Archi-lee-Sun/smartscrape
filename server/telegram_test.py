from telethon import TelegramClient
import os
from dotenv import load_dotenv

load_dotenv()

api_id = os.getenv("TELEGRAM_API_ID")
api_hash = os.getenv("TELEGRAM_API_HASH")

client = TelegramClient("smartscrape_session", api_id, api_hash)

async def main():
    me = await client.get_me()
    print(f"Logged in as: {me.first_name}")

with client:
    client.loop.run_until_complete(main())