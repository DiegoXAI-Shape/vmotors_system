"""Conexion de solo-uso-local a la base de datos SQLite de VMotors."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = BACKEND_DIR.parent / "database" / "vmotors.db"


def db_path() -> Path:
    return Path(os.getenv("VMOTORS_DB_PATH", str(DEFAULT_DB_PATH)))


def get_connection() -> sqlite3.Connection:
    path = db_path()
    if not path.exists():
        raise FileNotFoundError(
            f"No se encontró la base de datos en '{path}'. "
            "Genérela primero con: python database/seed_sqlite.py --reset --yes"
        )
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def query_all(sql: str, params: tuple = ()) -> list[dict]:
    con = get_connection()
    try:
        cur = con.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()


def query_one(sql: str, params: tuple = ()) -> dict | None:
    con = get_connection()
    try:
        cur = con.execute(sql, params)
        row = cur.fetchone()
        return dict(row) if row else None
    finally:
        con.close()
