"""Handles the SQLite database used by the SQL agent.

On first run this downloads the public Chinook sample database
(a small digital-media-store DB) so the chatbot has something to query
out of the box. To use your own database, just set DB_PATH to point to
an existing .db file (see .env.example).
"""

import os
import pathlib
import sqlite3

import requests

_DEFAULT_DB_PATH = pathlib.Path(__file__).parent.parent / "data" / "Chinook.db"
DB_PATH = pathlib.Path(os.getenv("DB_PATH", str(_DEFAULT_DB_PATH)))
DB_URL = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"


def ensure_database() -> pathlib.Path:
    """Make sure a SQLite database file exists at DB_PATH, downloading the
    sample Chinook database if nothing is there yet."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DB_PATH.exists():
        response = requests.get(DB_URL, timeout=60)
        response.raise_for_status()
        DB_PATH.write_bytes(response.content)
    return DB_PATH


def get_connection() -> sqlite3.Connection:
    ensure_database()
    return sqlite3.connect(DB_PATH)
