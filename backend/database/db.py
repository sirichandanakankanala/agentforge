from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "data" / "agentforge.db"
SCHEMA_PATH = BASE_DIR / "database" / "schema.sql"

_connection_string = os.getenv("DATABASE_URL")


def get_db_connection() -> Any:
    """
    Creates and returns a connection to the database.
    If DATABASE_URL is set, connects to PostgreSQL.
    Otherwise, connects to a local SQLite database.
    """
    if _connection_string and ("postgres" in _connection_string or "postgresql" in _connection_string):
        return psycopg2.connect(_connection_string)
    else:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(DB_PATH))
        # Enable dictionary-like row factory for SQLite
        conn.row_factory = sqlite3.Row
        return conn


def is_sqlite_connection(conn: Any) -> bool:
    return isinstance(conn, sqlite3.Connection)


def execute_query(query: str, params: Optional[tuple | list] = None) -> None:
    """
    Executes a modifying query (INSERT, UPDATE, DELETE).
    """
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        is_sqlite = is_sqlite_connection(conn)
        
        # Translate placeholder for SQLite
        if is_sqlite:
            query = query.replace("%s", "?")
            
        cur.execute(query, params or ())
        conn.commit()
    finally:
        conn.close()


def execute_read(query: str, params: Optional[tuple | list] = None) -> List[Dict[str, Any]]:
    """
    Executes a read query (SELECT) and returns rows as dictionaries.
    """
    conn = get_db_connection()
    try:
        is_sqlite = is_sqlite_connection(conn)
        if is_sqlite:
            cur = conn.cursor()
            query = query.replace("%s", "?")
            cur.execute(query, params or ())
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        else:
            # PostgreSQL RealDictCursor returns dicts
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute(query, params or ())
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    finally:
        conn.close()


def init_db() -> None:
    """
    Initializes database tables by running the schema.sql file.
    """
    if not SCHEMA_PATH.exists():
        print(f"Warning: Schema file not found at {SCHEMA_PATH}")
        return

    schema_content = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = get_db_connection()
    try:
        is_sqlite = is_sqlite_connection(conn)
        cur = conn.cursor()

        # Adjust schema keywords between Postgres and SQLite
        if is_sqlite:
            schema_content = schema_content.replace("SERIAL PRIMARY KEY", "INTEGER PRIMARY KEY AUTOINCREMENT")
        else:
            schema_content = schema_content.replace("INTEGER PRIMARY KEY AUTOINCREMENT", "SERIAL PRIMARY KEY")

        # Execute statements
        if is_sqlite:
            cur.executescript(schema_content)
        else:
            cur.execute(schema_content)
            
        conn.commit()
        print("Database initialized successfully.")
    except Exception as e:
        print(f"Error initializing database: {e}")
        conn.rollback()
    finally:
        conn.close()

# Run initialization on import
init_db()
