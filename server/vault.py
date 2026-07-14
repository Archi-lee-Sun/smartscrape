import sqlite3
from contextlib import closing
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "vault.db"

def init_vault() :
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.cursor()

            cursor.execute("""
                CREATE TABLE IF NOT exists vault_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_type TEXT NOT NULL,
                    source_name TEXT NOT NULL,
                    title TEXT NOT NULL,
                    content TEXT NOT NULL,
                    url TEXT NOT NULL,
                    published_at TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    cluster_size INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
                )
                """)
            
            cursor.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS vault_fts USING fts5(
                        title , summary , content,
                        content = 'vault_entries', content_rowid = 'id'
                )
                """)
            
            cursor.executescript("""
                CREATE TRIGGER IF NOT EXISTS vault_ai AFTER INSERT ON vault_entries BEGIN
                    INSERT INTO vault_fts(rowid , title , summary , content)
                    VALUES (new.id , new.title , new.summary , new.content);
                END;

                CREATE TRIGGER IF NOT EXISTS vault_ad AFTER DELETE ON vault_entries BEGIN
                    INSERT INTO vault_fts(vault_fts , rowid , title , summary , content)
                    VALUES ('delete' , old.id , old.title , old.summary , old.content);
                END;             
                
                CREATE TRIGGER IF NOT EXISTS vault_au AFTER UPDATE ON vault_entries BEGIN
                    INSERT INTO vault_fts(vault_fts , rowid , title , summary , content)
                    VALUES ('delete' , old.id , old.title , old.summary , old.content);
                    INSERT INTO vault_fts(rowid , title , summary , content)
                    VALUES (new.id , new.title , new.summary , new.content);
                END;
                """)


def save_to_vault(
    source_type: str,
    source_name: str,
    title: str,
    content: str,
    url: str,
    published_at: datetime,
    fetched_at: datetime,
    summary: str,
    mode: str,
    cluster_size: int,
) -> None:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            conn.execute(
                """
                INSERT INTO vault_entries (
                    source_type, source_name, title, content, url,
                    published_at, fetched_at, summary, mode, cluster_size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    source_type, source_name, title, content, str(url),
                    published_at.isoformat(), fetched_at.isoformat(),
                    summary, mode, cluster_size,
                ),
            )


def delete_entry(entry_id: int) -> bool:
    with closing(sqlite3.connect(DB_PATH)) as conn:
        with conn:
            cursor = conn.execute(
                "DELETE FROM vault_entries WHERE id = ?",
                (entry_id,),
            )
            return cursor.rowcount > 0