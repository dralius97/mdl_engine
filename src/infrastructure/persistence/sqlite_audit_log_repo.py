from typing import List, Dict, Any
from ...infrastructure.persistence.database import get_sqlite_connection

class SQLiteAuditLogRepository:
    def save_translation_log(self, dbname: str, hash_sql: str, executable_sql: str):
        """Mencatat riwayat translasi dari Hash SQL ke Executable SQL."""
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO sql_translation_logs (dbname, hash_sql, executable_sql)
            VALUES (?, ?, ?);
        """, (dbname.lower(), hash_sql, executable_sql))
        conn.commit()
        conn.close()

    def get_logs_by_dbname(self, dbname: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Mengambil riwayat log translasi SQL terbaru."""
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, dbname, hash_sql, executable_sql, created_at 
            FROM sql_translation_logs 
            WHERE dbname = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        """, (dbname.lower(), limit))
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]