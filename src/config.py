import os
from pathlib import Path

class Config:
    # Direktori kerja internal aplikasi di folder user home
    BASE_DIR = Path.home() / ".mdlEngine"
    @classmethod
    def get_db_path(cls) -> str:
        db_path = Path(
            os.getenv("MDL_ENGINE_DB_PATH", str(cls.BASE_DIR / "database" / "metadata.db"))
            )
        db_path.parent.mkdir(parents=True, exist_ok=True)
        return str(db_path)
    @classmethod
    def get_output_dir(cls) -> str:
        output_path = cls.BASE_DIR / "outputs"
        output_path.mkdir(parents=True, exist_ok=True)
        return str(output_path)