import asyncio
from .aggregator import aggregate_all_sources          
from .dedup.similarity import group_duplicates    
from .groq_client import synthesize_cluster, get_mode_for_cluster  

async def main():
    items = await aggregate_all_sources()
    groups = group_duplicates(items, threshold=0.82)
    multi_clusters = [g for g in groups if len(g) > 1]

    for group in multi_clusters:
        mode = get_mode_for_cluster(group)
        summary = synthesize_cluster(group)

        print(f"\n--- cluster size {len(group)} | mode: {mode} ---")
        print("SOURCES:")
        for item in group:
            print(f"  [{item.source_name}] {item.title}")
        print(f"SUMMARY:\n{summary}")

if __name__ == "__main__":
    asyncio.run(main())