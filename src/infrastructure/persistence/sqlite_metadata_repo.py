import json
from typing import Dict, Any, List, Optional
from .database import get_sqlite_connection
from ..storage.file_storage import FileStorageAdapter

class SQLiteMetadataRepository:
    def __init__(self):
        self.file_storage = FileStorageAdapter()

    def save_metadata(self, dbname: str, mdl_data: Dict[str, Any], hashtable_data: Dict[str, str]):
        dbname = dbname.lower()
        
        # 1. Simpan MDL sebagai File Mentah di Disk
        self.file_storage.save_mdl_file(dbname, mdl_data)

        # 2. Simpan Hashtable ke SQLite untuk Fast Index Lookup
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        
        # Clear hashtable lama untuk dbname ini jika re-sync
        cursor.execute("DELETE FROM hashtable_store WHERE dbname = ?", (dbname,))
        
        records = [(dbname, hash_id, full_path) for hash_id, full_path in hashtable_data.items()]
        cursor.executemany("""
            INSERT INTO hashtable_store (dbname, hash_id, full_path)
            VALUES (?, ?, ?);
        """, records)
        
        conn.commit()
        conn.close()

    def get_mdl_raw(self, dbname: str) -> Optional[str]:
        """Membaca isi file MDL mentah untuk disuapkan ke LLM."""
        return self.file_storage.read_mdl_content(dbname)

    def get_hashtable(self, dbname: str) -> Dict[str, str]:
        """Lookup hashtable kilat via Index SQLite."""
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT hash_id, full_path FROM hashtable_store WHERE dbname = ?", (dbname.lower(),))
        rows = cursor.fetchall()
        conn.close()
        return {row["hash_id"]: row["full_path"] for row in rows}

    def save_relations(self, dbname: str, relations_data: List[Dict[str, Any]]):
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO relation_store (dbname, relations_json, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(dbname) DO UPDATE SET
                relations_json = excluded.relations_json,
                updated_at = CURRENT_TIMESTAMP;
        """, (dbname.lower(), json.dumps(relations_data)))
        conn.commit()
        conn.close()

    def get_relations(self, dbname: str) -> List[Dict[str, Any]]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT relations_json FROM relation_store WHERE dbname = ?", (dbname.lower(),))
        row = cursor.fetchone()
        conn.close()
        return json.loads(row["relations_json"]) if row else []

    def save_checksum(self, dbname: str, checksum: str):
        """Menyimpan hash checksum skema DB ke SQLite."""
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO checksum_store (dbname, checksum, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(dbname) DO UPDATE SET
                checksum = excluded.checksum,
                updated_at = CURRENT_TIMESTAMP;
        """, (dbname.lower(), checksum))
        conn.commit()
        conn.close()
    
    def get_checksum(self, dbname: str) -> Optional[str]:
        """Membaca checksum terakhir untuk dbname tertentu."""
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT checksum FROM checksum_store WHERE dbname = ?", (dbname.lower(),))
        row = cursor.fetchone()
        conn.close()
        return row["checksum"] if row else None