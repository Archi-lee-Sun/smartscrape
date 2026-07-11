from .vault import init_vault, save_to_vault
from .vault_queries import search_vault, get_all_entries, get_full_entry
from datetime import datetime, timezone

class FakeItem:
    source_type = "rss"
    source_name = "BBC Sport"
    title = "Chelsea sign Quenda"
    content = "Chelsea announce the signing of Sporting winger Geovany Quenda."
    url = "https://example.com/quenda"
    published_at = datetime.now(timezone.utc)
    fetched_at = datetime.now(timezone.utc)

init_vault()
save_to_vault(FakeItem(), summary="Chelsea signed Quenda for £40m.", mode="short", cluster_size=3)

results = get_all_entries()
for row in results:
    print(dict(row))
print("SEARCH 'chelsea':", search_vault("chelsea"))
print("SEARCH 'nonexistent':", search_vault("nonexistent"))
print("FULL ENTRY id=1:", get_full_entry(1))
print("FULL ENTRY id=9999:", get_full_entry(9999))