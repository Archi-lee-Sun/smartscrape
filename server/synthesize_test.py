import asyncio

from .aggregator import aggregate_all_sources
from .dedup.similarity import group_duplicates, select_representative_items
from .groq_client import synthesize_cluster
from .routing import get_mode_for_cluster
from .vault import init_vault, save_to_vault


def print_cluster(group, mode: str, summary: str) -> None:
    print(f"\n--- cluster size {len(group)} | mode: {mode} ---")
    print("SOURCES:")
    for item in group:
        print(f"  [{item.source_type}/{item.source_name}] {item.title}")
    print(f"\nSUMMARY:\n{summary}\n")


async def main() -> None:
    init_vault()

    items = await aggregate_all_sources()
    groups = group_duplicates(items, threshold=0.82)

    processed_count = 0
    kept_count = 0
    discarded_count = 0
    skipped_count = 0

    for group in groups[:15]:
        processed_count += 1

        try:
            mode = get_mode_for_cluster(group)
            summary = synthesize_cluster(group)
        except Exception as e:
            print(f"\nWARNING: error synthesizing cluster: {e}")
            skipped_count += 1
            continue

        if summary is None:
            print("\nWARNING: synthesis failed for cluster; skipping.")
            skipped_count += 1
            continue

        print_cluster(group, mode, summary)

        keep = input("Keep this? (y/n): ").strip().lower()
        if keep in ("y" , "yes") :
            representative_item = select_representative_items([group])[0]
            save_to_vault(representative_item, summary, mode, len(group))
            kept_count += 1
            print("Saved.")
        else:
            discarded_count += 1
            print("Discarded.")

    print("\n--- run summary ---")
    print(f"Processed clusters: {processed_count}")
    print(f"Kept: {kept_count}")
    print(f"Discarded: {discarded_count}")
    print(f"Skipped due to synthesis failure: {skipped_count}")


if __name__ == "__main__":
    asyncio.run(main())
