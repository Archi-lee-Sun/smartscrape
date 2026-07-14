import asyncio

from server.aggregator import aggregate_all_sources


async def main() -> None:
    items = await aggregate_all_sources()

    rss_count = 0
    for item in items:
        if item.source_type != "rss":
            continue

        print("=" * 80)
        print(f"Source: {item.source_name}")
        print(f"Title: {item.title}")
        print("Content:")
        print(item.content)
        print(f"Content character length: {len(item.content)}")
        print(f"Title character length: {len(item.title)}")

        rss_count += 1
        if rss_count == 8:
            break

    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
