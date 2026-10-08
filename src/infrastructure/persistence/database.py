import sqlite3
import os
from ...config import Config

def get_sqlite_connection() -> sqlite3.Connection:
    db_path = Config.get_db_path()
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_sqlite_connection()
    cursor = conn.cursor()

    # 1. Connection Registry
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS connection_registry (
            dbname TEXT PRIMARY KEY,
            host TEXT NOT NULL,
            port INTEGER NOT NULL DEFAULT 5432,
            db_user TEXT NOT NULL,
            dialect TEXT NOT NULL DEFAULT 'postgresql',
            schema_name TEXT,
            connection_uri TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 2. Hashtable Store (Relational Lookup untuk SQLTranslator)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS hashtable_store (
            dbname TEXT NOT NULL,
            hash_id TEXT NOT NULL,
            full_path TEXT NOT NULL,
            PRIMARY KEY (dbname, hash_id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_hashtable_lookup ON hashtable_store(dbname, hash_id);")

    # 3. Relations Store
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS relation_store (
            dbname TEXT PRIMARY KEY,
            relations_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 4. Audit Log
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sql_translation_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dbname TEXT NOT NULL,
            hash_sql TEXT NOT NULL,
            executable_sql TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # 5. Checksum Store (Untuk Lazy Re-ingest)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checksum_store (
            dbname TEXT PRIMARY KEY,
            checksum TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    conn.commit()
    conn.close()
