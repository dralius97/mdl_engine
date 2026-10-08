from typing import Dict
import sqlglot
from sqlglot import exp

DELIMITER = "::"

def normalize_dialect(dialect: str) -> str:
    if not dialect:
        return "postgres"
    mapping = {
        "postgresql": "postgres", "postgres": "postgres",
        "mysql": "mysql", "sqlite": "sqlite",
        "duckdb": "duckdb", "oracle": "oracle",
        "mssql": "tsql", "sqlserver": "tsql"
    }
    return mapping.get(str(dialect).lower().strip(), "postgres")

def translate_hash_sql(
    hash_sql: str, 
    hashmap_dict: Dict[str, str], 
    dialect: str = "postgres"
) -> str:
    """
    Pure Function: Mentranslasikan SQL ber-Hash menjadi SQL asli.
    Menggunakan DELIMITER '::' untuk ekstraksi identifier terakhir.
    """
    lookup = {
        h_id: full_path.split(DELIMITER)[-1] 
        for h_id, full_path in hashmap_dict.items()
    }

    expression = sqlglot.parse_one(hash_sql)

    def transform(node):
        if isinstance(node, exp.Table) and node.name in lookup:
            node.set("this", exp.to_identifier(lookup[node.name]))
        elif isinstance(node, exp.Column) and node.name in lookup:
            node.set("this", exp.to_identifier(lookup[node.name]))
        return node

    translated_tree = expression.transform(transform)
    return translated_tree.sql(dialect=normalize_dialect(dialect))