import sqlite3
from contextlib import closing
from .vault import DB_PATH

def search_vault(query: str) -> list[sqlite3.Row]:
    clean_query = query.strip()
    if not clean_query:
        return []

    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            cursor = conn.cursor()
            try:
                cursor.execute(
                    """
                    SELECT
                        vault_entries.id,
                        vault_entries.title,
                        vault_entries.created_at
                    FROM vault_fts
                    JOIN vault_entries ON vault_fts.rowid = vault_entries.id
                    WHERE vault_fts MATCH ?
                    ORDER BY bm25(vault_fts)
                    """,
                    (f'{clean_query}*',),
                )
                return cursor.fetchall()
            except sqlite3.OperationalError:
                return []
            

def get_all_entries() -> list[sqlite3.Row]:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, created_at
                FROM vault_entries
                ORDER BY created_at DESC
                """)
            
            return cursor.fetchall()
        
        
def get_full_entry(entry_id: int) -> sqlite3.Row | None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        conn.row_factory = sqlite3.Row
        with conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT * FROM vault_entries
                WHERE id = ?
                """,
                (entry_id,),
            )
            return cursor.fetchone()
