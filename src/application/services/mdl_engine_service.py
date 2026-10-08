from typing import Dict, Any, Optional
import yaml
from ...domain.transformations.sql_translator import translate_hash_sql
from ...infrastructure.persistence.sqlite_metadata_repo import SQLiteMetadataRepository
from ...infrastructure.persistence.sqlite_audit_log_repo import SQLiteAuditLogRepository
from ...infrastructure.persistence.sqlite_connection_repo import SQLiteConnectionRepository

class MDLEngineService:
    def __init__(
        self,
        metadata_repo: SQLiteMetadataRepository,
        audit_log_repo: SQLiteAuditLogRepository,
        connection_repo: SQLiteConnectionRepository
    ):
        self.metadata_repo = metadata_repo
        self.audit_log_repo = audit_log_repo
        self.connection_repo = connection_repo

    def get_context(self, dbname: str) -> str:
        """
        Mengambil gabungan konteks lengkap: 
        Full Hashtable Mapping (Hash ID <-> Path/Name asli), MDL Schema, dan Verified Relations.
        """
        dbname = dbname.lower().strip()
        mdl_raw = self.metadata_repo.get_mdl_raw(dbname)
        full_hashmap = self.metadata_repo.get_hashtable(dbname)
        
        if not mdl_raw or not full_hashmap:
            return f"Error: Metadata MDL atau Hashmap untuk database '{dbname}' tidak ditemukan."

        try:
            mdl_data = yaml.safe_load(mdl_raw) or {}
            relations_data = self.metadata_repo.get_relations(dbname)
            
            # Format hashtable agar sangat mudah dibaca & dipahami LLM Agent
            formatted_hashtable = {
                "tables": {},
                "columns": {}
            }

            for hash_id, full_path in full_hashmap.items():
                parts = full_path.split("::")
                # Format full_path: dbname::schema::table::column ATAU dbname::schema::table
                if len(parts) == 3:
                    formatted_hashtable["tables"][hash_id] = f"{parts[1]}::{parts[2]}" # schema::table
                elif len(parts) == 4:
                    formatted_hashtable["columns"][hash_id] = f"{parts[2]}::{parts[3]}" # table::column
                    
            combined_context = {
                "database": dbname,
                "hashtable": formatted_hashtable,
                "mdl": mdl_data,
                "relations": [r for r in relations_data if r.get("status") == "verified"],
            }

            return yaml.dump(combined_context, sort_keys=False, default_flow_style=False)

        except Exception as e:
            return f"Error loading context for '{dbname}': {str(e)}"

    def translate_and_log_sql(self, dbname: str, hash_sql: str) -> str:
        """
        Mentranslasikan Hash SQL menjadi Executable SQL dan mencatatnya di Audit Log.
        """
        dbname = dbname.lower().strip()
        hashmap = self.metadata_repo.get_hashtable(dbname)

        if not hashmap:
            return f"Error: Hashmap lookup untuk database '{dbname}' tidak ditemukan."

        try:
            # Ambil dialect dari koneksi tersimpan (fallback ke postgres)
            conn_info = self.connection_repo.get_connection_details(dbname)
            dialect = conn_info.get("dialect", "postgres") if conn_info else "postgres"

            # 1. Pure FP Translation
            executable_sql = translate_hash_sql(
                hash_sql=hash_sql, 
                hashmap_dict=hashmap, 
                dialect=dialect
            )

            # 2. Side-Effect: Save Audit Log
            self.audit_log_repo.save_translation_log(
                dbname=dbname,
                hash_sql=hash_sql,
                executable_sql=executable_sql
            )

            return executable_sql

        except Exception as e:
            return f"Error translating SQL: {str(e)}"