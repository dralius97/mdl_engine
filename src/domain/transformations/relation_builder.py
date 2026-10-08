from typing import Dict, List, Any

def determine_join_type(from_col_meta: Dict[str, Any]) -> str:
    """
    Jika kolom FK asal bersifat UNIQUE atau Primary Key, 
    maka relasinya adalah ONE_TO_ONE, selain itu MANY_TO_ONE.
    """
    is_pk = from_col_meta.get("is_primary_key", False)
    is_unique = from_col_meta.get("is_unique", False)
    
    if is_pk or is_unique:
        return "ONE_TO_ONE"
    return "MANY_TO_ONE"


def extract_relations_from_mdl(
    mdl_data: Dict[str, Any], 
    existing_relations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    updated_rels = list(existing_relations)
    existing_ids = {r["id"] for r in updated_rels}

    schemas = mdl_data.get("schemas", {})

    for schema_name, schema_data in schemas.items():
        tables = schema_data.get("tables", {})
        for tbl_hash, tbl_data in tables.items():
            columns = tbl_data.get("columns", {})
            
            for fk in tbl_data.get("foreign_keys", []):
                constrained_cols = fk.get("constrained_columns", [])
                referred_cols = fk.get("referred_columns", [])
                ref_tbl_hash = fk.get("referred_table")

                if not (constrained_cols and referred_cols and ref_tbl_hash):
                    continue

                from_col_hash = constrained_cols[0]
                to_col_hash = referred_cols[0]
                
                # Deteksi metadata kolom asal untuk menentukan kardinalitas
                from_col_meta = columns.get(from_col_hash, {})
                join_type = determine_join_type(from_col_meta)

                rel_id = f"rel_{tbl_hash}_{from_col_hash}__to__{ref_tbl_hash}_{to_col_hash}"

                if rel_id not in existing_ids:
                    updated_rels.append({
                        "id": rel_id,
                        "from_column_hash": from_col_hash,
                        "to_column_hash": to_col_hash,
                        "from_table_hash": tbl_hash,
                        "to_table_hash": ref_tbl_hash,
                        "join_type": join_type,  
                        "source": "db_fk",
                        "status": "verified"
                    })
                    existing_ids.add(rel_id)

    return updated_rels