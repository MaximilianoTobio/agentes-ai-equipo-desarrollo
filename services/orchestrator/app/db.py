import os
from pathlib import Path
from typing import Optional

class DBConfigError(RuntimeError):
    pass

def read_password_from_file(path: str) -> str:
    """
    Lee la contraseña desde un archivo (secret) sin agregar saltos de línea.
    Lanza DBConfigError si el archivo no existe o está vacío.
    """
    try:
        p = Path(path)
        if not p.exists():
            raise DBConfigError(f"Secret file not found: {path}")
        pwd = p.read_text(encoding="utf-8").strip()
        if not pwd:
            raise DBConfigError("Secret file is empty")
        return pwd
    except DBConfigError:
        raise
    except Exception as exc:
        raise DBConfigError(f"Error reading secret file: {exc}") from exc

def build_database_url(
    user: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[str] = None,
    dbname: Optional[str] = None,
    password_file_env: str = "DB_PASSWORD_FILE",
    driver: str = "postgresql",
) -> str:
    """
    Construye DATABASE_URL leyendo la contraseña desde DB_PASSWORD_FILE.
    Variables de entorno esperadas si no se pasan como parámetros:
    - DB_USER, DB_HOST, DB_PORT, DB_NAME, DB_PASSWORD_FILE
    """
    user = user or os.getenv("DB_USER")
    host = host or os.getenv("DB_HOST", "localhost")
    port = port or os.getenv("DB_PORT", "5432")
    dbname = dbname or os.getenv("DB_NAME", "postgres")
    pwd_path = os.getenv(password_file_env)

    if not user or not dbname or not host or not port:
        raise DBConfigError("Missing DB config envs (DB_USER/DB_NAME/DB_HOST/DB_PORT)")
    if not pwd_path:
        raise DBConfigError(f"Missing env {password_file_env}")

    password = read_password_from_file(pwd_path)
    return f"{driver}://{user}:{password}@{host}:{port}/{dbname}"
