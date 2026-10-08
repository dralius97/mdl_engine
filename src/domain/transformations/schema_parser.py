from typing import Dict, Any, Tuple
from ..transformations.hasher import generate_shake128_hash


def parse_raw_schema_to_mdl(
    dbname: str,
    raw_schemas: Dict[str, Any]
) -> Tuple[Dict[str, Any], Dict[str, str]]:
    """
    Pure Function: Mengubah dict skema mentah DB menjadi tuple:
    (mdl_structure, flat_hashmap)
    """
    schemas_data = {}
    flat_hashmap = {}

    for schema, tables in raw_schemas.items():
        tables_data = {}

        for table_name, table_info in tables.items():
            table_path = f"{dbname}::{schema}::{table_name}"
            table_hash = generate_shake128_hash(table_path)
            flat_hashmap[table_hash] = table_path

            raw_pks = table_info.get("primary_keys", [])
            col_name_to_hash = {}
            columns_data = {}

            for col in table_info.get("columns", []):
                col_name = col["name"]
                col_path = f"{table_path}::{col_name}"
                col_hash = generate_shake128_hash(col_path)

                col_name_to_hash[col_name] = col_hash
                flat_hashmap[col_hash] = col_path

                columns_data[col_hash] = {
                    "type": str(col["type"]),
                    "nullable": col["nullable"],
                    "is_primary_key": col_name in raw_pks,
                    "comment": col.get("comment")
                }

            pk_hashes = [
                col_name_to_hash[pk]
                for pk in raw_pks
                if pk in col_name_to_hash
            ]

            fk_info = []

            for fk in table_info.get("foreign_keys", []):
                ref_schema = fk.get("referred_schema") or schema
                ref_table = fk.get("referred_table")

                constrained_hashes = [
                    col_name_to_hash[c]
                    for c in fk.get("constrained_columns", [])
                    if c in col_name_to_hash
                ]

                referred_hashes = [
                    generate_shake128_hash(
                        f"{dbname}::{ref_schema}::{ref_table}::{rc}"
                    )
                    for rc in fk.get("referred_columns", [])
                ]

                ref_table_hash = generate_shake128_hash(
                    f"{dbname}::{ref_schema}::{ref_table}"
                )

                fk_info.append({
                    "constrained_columns": constrained_hashes,
                    "referred_schema": ref_schema,
                    "referred_table": ref_table_hash,
                    "referred_columns": referred_hashes
                })

            tables_data[table_hash] = {
                "comment": table_info.get("comment"),
                "primary_keys": pk_hashes,
                "foreign_keys": fk_info,
                "columns": columns_data
            }

        schemas_data[schema] = {"tables": tables_data}

    mdl_structure = {
        "mdl_id": f"mdl_{dbname}",
        "dbname": dbname,
        "schemas": schemas_data
    }

    return mdl_structure, flat_hashmap