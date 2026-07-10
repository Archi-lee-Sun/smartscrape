import asyncio
import sys
from collections import Counter

from ..aggregator import aggregate_all_sources
from .similarity import build_similarity_matrix, group_duplicates

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def preview_text(text: str, max_length: int = 160) -> str:
    single_line = " ".join(text.split())
    if len(single_line) <= max_length:
        return single_line
    return single_line[: max_length - 3] + "..."


async def main():
    items = await aggregate_all_sources()
    print(f"Total items: {len(items)}")

    matrix = build_similarity_matrix(items)
    groups = group_duplicates(items, threshold=0.82)

    sizes = Counter(len(group) for group in groups)
    size_summary = ", ".join(
        f"{size}: {count}" for size, count in sorted(sizes.items())
    )
    print(f"Cluster size distribution: {size_summary}")

    for group in groups:
        if len(group) > 1:
            print(f"\n--- cluster of {len(group)} ---")
            indices = [items.index(item) for item in group]
            for a in range(len(indices)):
                for b in range(a + 1, len(indices)):
                    score = matrix[indices[a]][indices[b]].item()
                    print(
                        f"  score {score:.4f}: "
                        f"{group[a].source_name} <-> {group[b].source_name}"
                    )
            for item in group:
                source = f"{item.source_type}/{item.source_name}"
                print(f"[{source}] \"{preview_text(item.content)}\"")


if __name__ == "__main__":
    asyncio.run(main())
