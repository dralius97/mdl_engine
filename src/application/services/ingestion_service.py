# src/semantic_layer/application/services/ingestion_service.py
from typing import Dict, Any, Optional
from ...domain.fp import pipe
from ...domain.transformations.hasher import calculate_schema_checksum
from ...domain.transformations.schema_parser import parse_raw_schema_to_mdl
from ...domain.transformations.relation_builder import extract_relations_from_mdl
from ...infrastructure.database.inspector import DatabaseInspectorAdapter
from ...infrastructure.persistence.sqlite_metadata_repo import SQLiteMetadataRepository
from ...infrastructure.persistence.sqlite_connection_repo import SQLiteConnectionRepository

class IngestionService:
    def __init__(
        self, 
        inspector: DatabaseInspectorAdapter,
        metadata_repo: SQLiteMetadataRepository,
        connection_repo: SQLiteConnectionRepository
    ):
        self.inspector = inspector
        self.metadata_repo = metadata_repo
        self.connection_repo = connection_repo

    def sync_database(
        self, 
        dbname: str, 
        host: str, 
        port: int, 
        db_user: str, 
        dialect: str, 
        schema_name: Optional[str], 
        connection_uri: str,
        force_reingest: bool = False
    ) -> Dict[str, Any]:
        """
        Orchestration pipeline untuk sync & ingestion metadata database.
        """
        dbname = dbname.lower().strip()

        # 1. Simpan/Update Registry Koneksi ke SQLite
        self.connection_repo.save_connection(
            dbname=dbname, host=host, port=port, 
            db_user=db_user, dialect=dialect, 
            schema_name=schema_name, connection_uri=connection_uri
        )

        # 2. Ambil raw schema dari DB target (I/O)
        raw_schemas = self.inspector.get_raw_schema(connection_uri, schema_name)

        # 3. Cek Checksum / Delta Perubahan (Lazy Re-ingest)
        current_checksum = calculate_schema_checksum(raw_schemas)
        existing_checksum = self.metadata_repo.get_checksum(dbname)

        if not force_reingest and existing_checksum == current_checksum:
            return {
                "status": "skipped",
                "message": f"Tidak ada perubahan skema pada '{dbname}'. Ingestion di-skip.",
                "checksum": current_checksum
            }

        # 4. Run Pure FP Transformations
        mdl_structure, flat_hashmap = parse_raw_schema_to_mdl(dbname, raw_schemas)

        existing_relations = self.metadata_repo.get_relations(dbname)
        updated_relations = extract_relations_from_mdl(mdl_structure, existing_relations)

        # 5. Persist ke Storage (File & SQLite)
        self.metadata_repo.save_metadata(dbname, mdl_structure, flat_hashmap)
        self.metadata_repo.save_relations(dbname, updated_relations)
        self.metadata_repo.save_checksum(dbname, current_checksum)

        return {
            "status": "success",
            "message": f"Berhasil meng-ingest metadata untuk database '{dbname}'.",
            "total_relations": len(updated_relations),
            "checksum": current_checksum
        }