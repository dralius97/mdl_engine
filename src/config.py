import os
from pathlib import Path

class Config:
    # Direktori kerja internal aplikasi di folder user home
    BASE_DIR = Path.home() / ".mdlEngine"
    @classmethod
    def get_db_path(cls) -> str:
        # Menjamin direktori ~/.semantic_layer/ terbuat otomatis
        cls.BASE_DIR.mkdir(parents=True, exist_ok=True)
        return str(cls.BASE_DIR / "metadata.db")

    @classmethod
    def get_output_dir(cls) -> str:
        output_path = cls.BASE_DIR / "outputs"
        output_path.mkdir(parents=True, exist_ok=True)
        return str(output_path)