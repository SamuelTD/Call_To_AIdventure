from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[2]

def project_path(relative_path: str) -> Path:
    return (PROJECT_ROOT / relative_path).resolve()

def env_project_path(env_var: str, default: str) -> Path:
    value = os.getenv(env_var, default)
    return project_path(value)