import hashlib
import json
from typing import Dict, Any

def generate_shake128_hash(path: str) -> str:
    """Mengubah string path identifier menjadi Hash ID (4 bytes hex / 8 karakter)."""
    clean_path = path.lower().strip()
    hash_hex = hashlib.shake_128(clean_path.encode('utf-8')).hexdigest(4)
    return f"h_{hash_hex}"

def calculate_schema_checksum(raw_schemas: Dict[str, Any]) -> str:
    """Mengalkulasi MD5 hash dari skema mentah untuk pengecekan delta perubahan."""
    schema_str = json.dumps(raw_schemas, sort_keys=True, default=str)
    return hashlib.sha256(schema_str.encode('utf-8')).hexdigest()