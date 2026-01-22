from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Tuple

def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS meta_semanal (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        colecao TEXT NOT NULL,
        meta INTEGER NOT NULL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_meta_semanal_colecao
    ON meta_semanal(colecao);
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS config (
        k TEXT PRIMARY KEY,
        v TEXT NOT NULL,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)
    conn.commit()

def set_config(conn: sqlite3.Connection, k: str, v: str) -> None:
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO config(k,v) VALUES(?,?)
    ON CONFLICT(k) DO UPDATE SET v=excluded.v, updated_at=CURRENT_TIMESTAMP;
    """, (k, v))
    conn.commit()

def get_config(conn: sqlite3.Connection, k: str, default: str|None=None) -> str|None:
    cur = conn.cursor()
    row = cur.execute("SELECT v FROM config WHERE k=?", (k,)).fetchone()
    return row[0] if row else default

def upsert_meta_semanal(conn: sqlite3.Connection, colecao: str, meta: int) -> None:
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO meta_semanal(colecao, meta) VALUES(?,?)
    ON CONFLICT(colecao) DO UPDATE SET meta=excluded.meta, updated_at=CURRENT_TIMESTAMP;
    """, (colecao, meta))
    conn.commit()

def delete_meta_semanal(conn: sqlite3.Connection, colecao: str) -> None:
    cur = conn.cursor()
    cur.execute("DELETE FROM meta_semanal WHERE colecao=?", (colecao,))
    conn.commit()

def list_metas(conn: sqlite3.Connection) -> list[dict]:
    cur = conn.cursor()
    rows = cur.execute("SELECT colecao, meta, updated_at FROM meta_semanal ORDER BY colecao").fetchall()
    return [dict(r) for r in rows]
