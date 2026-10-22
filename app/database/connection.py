"""Database connection manager for SQLite."""
import sqlite3
from pathlib import Path
from contextlib import contextmanager
from typing import Generator
from app.config import settings
from app.database.models import CREATE_TABLES_SQL


def get_db_path() -> Path:
    db_path = settings.DATABASE_PATH
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return db_path


def init_db(db_path: Path | None = None) -> None:
    """Initialize database tables."""
    target_path = db_path or get_db_path()
    target_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(target_path) as conn:
        conn.execute("PRAGMA journal_mode = WAL;")
        conn.execute("PRAGMA foreign_keys = ON;")
        conn.executescript(CREATE_TABLES_SQL)
        conn.commit()


@contextmanager
def get_db_connection(db_path: Path | None = None) -> Generator[sqlite3.Connection, None, None]:
    """Yield a SQLite connection with dict-like row access."""
    target_path = db_path or get_db_path()
    conn = sqlite3.connect(target_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
    finally:
        conn.close()
