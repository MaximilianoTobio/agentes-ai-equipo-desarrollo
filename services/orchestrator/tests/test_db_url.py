import os
import tempfile
from services.orchestrator.app.db import build_database_url, DBConfigError

def test_build_database_url_from_secret_file(tmp_path):
    # Creamos un secret file temporal
    secret = tmp_path / "pgpass"
    secret.write_text("S3cr3t!\n", encoding="utf-8")

    # Configuramos envs mínimas
    os.environ["DB_USER"] = "postgres"
    os.environ["DB_NAME"] = "orchestrator"
    os.environ["DB_HOST"] = "postgres"
    os.environ["DB_PORT"] = "5432"
    os.environ["DB_PASSWORD_FILE"] = str(secret)

    url = build_database_url()

    assert url == "postgresql://postgres:S3cr3t!@postgres:5432/orchestrator"

def test_missing_password_file_env_raises(tmp_path, monkeypatch):
    # Aseguramos que no existe la env DB_PASSWORD_FILE
    monkeypatch.delenv("DB_PASSWORD_FILE", raising=False)
    os.environ["DB_USER"] = "postgres"
    os.environ["DB_NAME"] = "orchestrator"
    os.environ["DB_HOST"] = "postgres"
    os.environ["DB_PORT"] = "5432"

    try:
        build_database_url()
        assert False, "Should have raised DBConfigError"
    except DBConfigError as e:
        assert "Missing env DB_PASSWORD_FILE" in str(e)
