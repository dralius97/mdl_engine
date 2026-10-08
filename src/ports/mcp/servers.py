import os
from typing import List, Dict, Any, Optional
from fastmcp import FastMCP

# Import Configuration & Persistence Init
from src.config import Config
from src.infrastructure.persistence.database import init_db

# Import Persistence Repositories
from src.infrastructure.persistence.sqlite_connection_repo import SQLiteConnectionRepository
from src.infrastructure.persistence.sqlite_metadata_repo import SQLiteMetadataRepository
from src.infrastructure.persistence.sqlite_audit_log_repo import SQLiteAuditLogRepository

# Import Infrastructure Adapters
from src.infrastructure.database.inspector import DatabaseInspectorAdapter

# Import Application Services
from src.application.services.ingestion_service import IngestionService
from src.application.services.mdl_engine_service import MDLEngineService

# 1. Inisialisasi Database SQLite Internal saat server startup
init_db()

# 2. Inisialisasi Repositories & Adapters (Dependency Injection)
connection_repo = SQLiteConnectionRepository()
metadata_repo = SQLiteMetadataRepository()
audit_log_repo = SQLiteAuditLogRepository()
inspector_adapter = DatabaseInspectorAdapter()

# 3. Inisialisasi Application Services
ingestion_service = IngestionService(
    inspector=inspector_adapter,
    metadata_repo=metadata_repo,
    connection_repo=connection_repo
)

mdl_engine_service = MDLEngineService(
    metadata_repo=metadata_repo,
    audit_log_repo=audit_log_repo,
    connection_repo=connection_repo
)

# 4. Inisialisasi FastMCP Server
mcp = FastMCP("mdl_engine_analyst")


# ==========================================
# MCP TOOLS DEFINITION
# ==========================================

@mcp.tool()
def list_connections() -> List[Dict[str, Any]]:
    """
    Mengembalikan daftar seluruh database yang terdaftar dan terhubung.
    TIDAK mengekspos password atau connection string sensitif.
    """
    return connection_repo.list_connections()


@mcp.tool()
def sync_database_metadata(
    alias: str,
    dbname: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = 5432,
    db_user: Optional[str] = None,
    password: Optional[str] = None,
    dialect: Optional[str] = "postgresql",
    schema_name: Optional[str] = None,
    connection_uri: Optional[str] = None,
    force_reingest: bool = False
) -> str:
    """
    Meng-ingest skema database target, membuat Hash ID, mengekstrak relasi FK,
    dan menyimpannya ke registry. Bisa menerima Host/Creds atau Connection URI.
    """
    alias = alias.lower().strip()

    # Resolve koneksi berdasarkan alias yang sudah terdaftar
    existing_conn = connection_repo.get_connection_details(alias)

    if existing_conn:
        dbname = existing_conn["dbname"]
        connection_uri = existing_conn["connection_uri"]
        host = existing_conn["host"]
        port = existing_conn["port"]
        db_user = existing_conn["db_user"]
        dialect = existing_conn["dialect"]
        schema_name = existing_conn.get("schema_name")

    else:
        # Belum ada koneksi → gunakan parameter yang diberikan agent
        if not connection_uri:
            if host and dbname and db_user and password:
                if dialect == "sqlite":
                    connection_uri = f"sqlite:///{dbname}.db"
                else:
                    connection_uri = (
                        f"{dialect}://{db_user}:{password}"
                        f"@{host}:{port}/{dbname}"
                    )
            else:
                return (
                    f"Error: Informasi koneksi untuk alias '{alias}' "
                    "tidak ditemukan. Mohon berikan detail koneksi."
                )

    if connection_uri is None:
        return f"Error: Connection URI untuk alias '{alias}' tidak ditemukan."    

    if dbname is None:
        return f"Error: Connection dbname untuk alias '{alias}' tidak ditemukan."
    
    try:
        result = ingestion_service.sync_database(
            dbname=dbname,
            alias=alias,
            host=host or "localhost",
            port=port or 5432,
            db_user=db_user or "unknown",
            dialect=dialect or "postgresql",
            schema_name=schema_name,
            connection_uri=connection_uri,
            force_reingest=force_reingest
        )
        return result["message"]
    except Exception as e:
        return f"Gagal melakukan sync database '{alias}': {str(e)}"

@mcp.tool()
def get_semantic_context(alias: str) -> str:
    """Mengambil seluruh konteks semantik ber-hash (MDL & Relasi) untuk database tertentu.
    Harus dipanggil LLM Agent sebelum menyusun query SQL.
    """
    return mdl_engine_service.get_context(alias)

@mcp.tool()
def parse_and_translate_sql(alias: str, hash_sql: str) -> str:
    """
    Mentranslasikan Hash SQL buatan LLM menjadi Executable SQL dengan identifier asli.
    Mencatat riwayat translasi ke audit log.
    """
    return mdl_engine_service.translate_and_log_sql(alias=alias, hash_sql=hash_sql)


@mcp.tool()
def save_dashboard_html(filename: str, html_content: str) -> str:
    """
    Menyimpan kode HTML5 dashboard interaktif yang dihasilkan Agent ke folder outputs.
    """
    try:
        output_dir = Config.get_output_dir()
        if not filename.endswith(".html"):
            filename += ".html"
            
        filepath = os.path.join(output_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
            
        return f"SUCCESS: Dashboard berhasil disimpan ke {filepath}."
    except Exception as e:
        return f"ERROR: Gagal menyimpan dashboard: {str(e)}"


def main():
    """Entry point CLI untuk menjalankan FastMCP server (Default Stdio)."""
    mcp.run()

if __name__ == "__main__":
    main()
