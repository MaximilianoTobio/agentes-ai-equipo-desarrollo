# services/orchestrator/tests/conftest.py
import sys
from pathlib import Path

# Subimos desde:
# tests -> orchestrator -> services -> (repo root)
REPO_ROOT = Path(__file__).resolve().parents[3]
repo_root_str = str(REPO_ROOT)

if repo_root_str not in sys.path:
    sys.path.insert(0, repo_root_str)

# sanity check: confirmamos que la carpeta "services" existe en el root del repo
assert (REPO_ROOT / "services").exists(), "No se encontró la carpeta 'services' en el root del repo"
