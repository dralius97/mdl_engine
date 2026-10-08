import json
from typing import Dict, Any, List, Optional
from .database import get_sqlite_connection
from ..storage.file_storage import FileStorageAdapter

class SQLiteMetadataRepository:
    def __init__(self):
        self.file_storage = FileStorageAdapter()

    def save_metadata( self, alias: str, mdl_data: Dict[str, Any], hashtable_data: Dict[str, str]):
        alias = alias.lower()

        # 1. Simpan MDL sebagai file mentah di disk
        self.file_storage.save_mdl_file(alias, mdl_data)

        # 2. Simpan hashtable ke SQLite untuk fast index lookup
        conn = get_sqlite_connection()
        cursor = conn.cursor()

        # Clear hashtable lama untuk alias ini jika re-sync
        cursor.execute( "DELETE FROM hashtable_store WHERE alias = ?", (alias,))

        records = [ (alias, hash_id, full_path) for hash_id, full_path in hashtable_data.items()]

        cursor.executemany(
            """INSERT INTO hashtable_store (alias, hash_id, full_path)
            VALUES (?, ?, ?);""",
            records
            )
        conn.commit()
        conn.close()

    def get_mdl_raw(self, alias: str) -> Optional[str]:
        """Membaca isi file MDL mentah untuk disuapkan ke LLM."""
        return self.file_storage.read_mdl_content(alias)

    def get_hashtable(self, alias: str) -> Dict[str, str]:
        """Lookup hashtable kilat via Index SQLite."""
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT hash_id, full_path FROM hashtable_store WHERE alias = ?", (alias.lower(),))
        rows = cursor.fetchall()
        conn.close()
        return {row["hash_id"]: row["full_path"] for row in rows}

    def save_relations(self, alias: str, relations_data: List[Dict[str, Any]]):
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO relation_store (alias, relations_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(alias) DO UPDATE SET
                relations_json = excluded.relations_json,
                updated_at = CURRENT_TIMESTAMP;
        """, (alias.lower(), json.dumps(relations_data)))
        conn.commit()
        conn.close()

    def get_relations(self, alias: str) -> List[Dict[str, Any]]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT relations_json FROM relation_store WHERE alias = ?", (alias.lower(),))
        row = cursor.fetchone()
        conn.close()
        return json.loads(row["relations_json"]) if row else []

    def save_checksum(self, alias: str, checksum: str):
        """Menyimpan hash checksum skema DB ke SQLite."""
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO checksum_store (alias, checksum, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(alias) DO UPDATE SET
                checksum = excluded.checksum,
                updated_at = CURRENT_TIMESTAMP;
        """, (alias.lower(), checksum))
        conn.commit()
        conn.close()
    
    def get_checksum(self, alias: str) -> Optional[str]:
        """Membaca checksum terakhir untuk alias tertentu."""
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT checksum FROM checksum_store WHERE alias = ?", (alias.lower(),))
        row = cursor.fetchone()
        conn.close()
        return row["checksum"] if row else None