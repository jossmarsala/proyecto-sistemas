
import os
import sys
import sqlite3
from pathlib import Path


def _resolve_db_path() -> Path:
    if os.environ.get("VERCEL") == "1":
        return Path("/tmp/faro.db")

    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent
    else:
        base = Path(__file__).resolve().parent.parent

    db_dir = base / "database"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "ventas.db"


DB_PATH: Path = _resolve_db_path()


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def run_migration(sql: str) -> None:
    conn = get_connection()
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()
