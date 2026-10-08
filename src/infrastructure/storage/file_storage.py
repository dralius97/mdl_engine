import os
import yaml
from typing import Dict, Any, Optional
from ...config import Config

class FileStorageAdapter:
    def __init__(self):
        self.config_dir = os.path.join(Config.BASE_DIR, "configs")
        os.makedirs(self.config_dir, exist_ok=True)

    def _get_mdl_filepath(self, dbname: str) -> str:
        return os.path.join(self.config_dir, f"local_mdl_{dbname.lower()}.yaml")

    def save_mdl_file(self, dbname: str, mdl_data: Dict[str, Any]) -> str:
        filepath = self._get_mdl_filepath(dbname)
        with open(filepath, "w", encoding="utf-8") as f:
            yaml.dump(mdl_data, f, sort_keys=False, default_flow_style=False)
        return filepath

    def read_mdl_content(self, dbname: str) -> Optional[str]:
        """Membaca mentah isi file YAML sebagai string untuk konteks LLM."""
        filepath = self._get_mdl_filepath(dbname)
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()