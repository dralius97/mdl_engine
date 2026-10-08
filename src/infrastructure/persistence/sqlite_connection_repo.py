from typing import List, Dict, Any, Optional
from .database import get_sqlite_connection

class SQLiteConnectionRepository:
    def save_connection(
        self, 
        dbname: str, 
        alias: str,
        host: str, 
        port: int, 
        db_user: str, 
        dialect: str, 
        schema_name: Optional[str], 
        connection_uri: str
    ):
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO connection_registry (dbname, alias, host, port, db_user, dialect, schema_name, connection_uri, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(alias) DO UPDATE SET
                dbname = excluded.dbname,
                host = excluded.host,
                port = excluded.port,
                db_user = excluded.db_user,
                dialect = excluded.dialect,
                schema_name = excluded.schema_name,
                connection_uri = excluded.connection_uri,
                updated_at = CURRENT_TIMESTAMP;
        """, (dbname, alias, host, port, db_user, dialect, schema_name, connection_uri))
        conn.commit()
        conn.close()

    def get_connection_uri(self, alias: str) -> Optional[str]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT connection_uri FROM connection_registry WHERE alias = ?", (alias.lower(),))
        row = cursor.fetchone()
        conn.close()
        return row["connection_uri"] if row else None

    def list_connections(self) -> List[Dict[str, Any]]:
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dbname, alias, host, port, db_user, dialect, schema_name, updated_at 
            FROM connection_registry
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    
    def get_connection_details(self, alias: str) -> Optional[Dict[str, Any]]:
        """Membaca detail koneksi lengkap (termasuk dialect & uri) berdasarkan alias."""
        conn = get_sqlite_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT dbname, alias, host, port, db_user, dialect, schema_name, connection_uri 
            FROM connection_registry 
            WHERE alias = ?
        """, (alias.lower(),))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None