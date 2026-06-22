"""
FARO – Database connection helper.

Replaces the ad-hoc sqlite3 open/close pattern in the old controlador_db.py
with a single source-of-truth for the DB path and a reusable connection factory.
"""

import os
import sys
import sqlite3
from pathlib import Path


def _resolve_db_path() -> Path:
    """
    Returns the correct absolute path to ventas.db regardless of whether
    we are running as a plain .py script, a frozen .exe, or via uvicorn.
    """
    if os.environ.get("VERCEL") == "1":
        return Path("/tmp/ventas.db")

    if getattr(sys, "frozen", False):
        # PyInstaller / frozen exe: db lives next to the executable
        base = Path(sys.executable).parent
    else:
        # Development / uvicorn: project root is two levels above this file
        # db/connection.py  → db/ → project root
        base = Path(__file__).resolve().parent.parent

    db_dir = base / "database"
    db_dir.mkdir(parents=True, exist_ok=True)
    return db_dir / "ventas.db"


DB_PATH: Path = _resolve_db_path()


def get_connection() -> sqlite3.Connection:
    """
    Opens and returns a sqlite3 connection with:
    - Foreign key enforcement enabled
    - Row factory set to sqlite3.Row (dict-like row access)
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def run_migration(sql: str) -> None:
    """
    Executes a multi-statement SQL string (DDL / seed data) inside a
    single connection. Used during app startup to apply the full schema.
    """
    conn = get_connection()
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()
