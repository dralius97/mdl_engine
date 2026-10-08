# src/semantic_layer/infrastructure/database/inspector.py
from typing import Dict, Any, Optional
from sqlalchemy import create_engine, inspect

class DatabaseInspectorAdapter:
    def get_raw_schema(self, connection_uri: str, schema_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Membaca metadata DB mentah via SQLAlchemy Inspector.
        Mengembalikan struktur dict murni yang siap di-parse oleh domain schema_parser.
        """
        engine = create_engine(connection_uri)
        inspector = inspect(engine)

        if schema_name is None:
            schema_names = [
                s for s in inspector.get_schema_names()
                if s not in ("information_schema", "pg_catalog") and not s.startswith("pg_")
            ]
        else:
            schema_names = [schema_name]

        raw_schemas = {}

        for schema in schema_names:
            tables_data = {}
            table_names = inspector.get_table_names(schema=schema)

            for table in table_names:
                pk_constraint = inspector.get_pk_constraint(table, schema=schema)
                raw_pks = pk_constraint.get("constrained_columns", []) if pk_constraint else []

                columns_data = []
                for col in inspector.get_columns(table, schema=schema):
                    columns_data.append({
                        "name": col["name"],
                        "type": str(col["type"]),
                        "nullable": col["nullable"],
                        "comment": col.get("comment")
                    })

                fk_data = []
                for fk in inspector.get_foreign_keys(table, schema=schema):
                    fk_data.append({
                        "constrained_columns": fk.get("constrained_columns", []),
                        "referred_schema": fk.get("referred_schema") or schema,
                        "referred_table": fk.get("referred_table"),
                        "referred_columns": fk.get("referred_columns", [])
                    })

                table_comment = inspector.get_table_comment(table, schema=schema)
                doc = table_comment.get("text") if table_comment else None

                tables_data[table] = {
                    "comment": doc,
                    "primary_keys": raw_pks,
                    "columns": columns_data,
                    "foreign_keys": fk_data
                }

            raw_schemas[schema] = tables_data

        return raw_schemas