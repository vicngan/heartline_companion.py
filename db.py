"""
SQLite persistence helpers for Heartline Care Companion.

Tables:
- users: authentication + encryption salts
- check_ins / appointments / symptoms: user-owned entries
- devices: Expo push tokens for notifications
"""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

DB_PATH = Path(os.getenv("HEARTLINE_DB_PATH", "heartline.db"))


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = _connect()
    with conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL UNIQUE,
                full_name TEXT,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                encryption_salt TEXT NOT NULL,
                created_at TEXT NOT NULL,
                theme_preference TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_tokens (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token_hash TEXT NOT NULL UNIQUE,
                encrypted_key TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        try:
            conn.execute("ALTER TABLE users ADD COLUMN theme_preference TEXT")
        except sqlite3.OperationalError:
            pass
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS check_ins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                mood INTEGER,
                energy INTEGER,
                schedule TEXT,
                note_encrypted TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title_encrypted TEXT,
                category TEXT,
                provider_encrypted TEXT,
                date TEXT NOT NULL,
                notes_encrypted TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS symptoms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symptom_encrypted TEXT,
                severity INTEGER,
                notes_encrypted TEXT,
                date TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                label TEXT,
                expo_token TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
    conn.close()


# --- User helpers ---------------------------------------------------------


def create_user(
    email: str,
    full_name: str,
    password_hash: str,
    password_salt: str,
    encryption_salt: str,
) -> int:
    conn = _connect()
    with conn:
        cursor = conn.execute(
            """
            INSERT INTO users (email, full_name, password_hash, password_salt, encryption_salt, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (email, full_name, password_hash, password_salt, encryption_salt, datetime.utcnow().isoformat()),
        )
        user_id = cursor.lastrowid
    conn.close()
    return user_id


def get_user_by_email(email: str) -> Optional[sqlite3.Row]:
    conn = _connect()
    row = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int) -> Optional[sqlite3.Row]:
    conn = _connect()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return row


# --- Data fetch helpers ---------------------------------------------------


def fetch_check_ins(user_id: int, limit: int = 200) -> List[sqlite3.Row]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM check_ins WHERE user_id = ? ORDER BY timestamp ASC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return rows


def fetch_appointments(user_id: int) -> List[sqlite3.Row]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM appointments WHERE user_id = ? ORDER BY date ASC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def fetch_symptoms(user_id: int) -> List[sqlite3.Row]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM symptoms WHERE user_id = ? ORDER BY date DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def fetch_devices(user_id: int) -> List[sqlite3.Row]:
    conn = _connect()
    rows = conn.execute(
        "SELECT * FROM devices WHERE user_id = ? ORDER BY created_at DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def update_user_theme(user_id: int, theme_key: str) -> None:
    conn = _connect()
    with conn:
        conn.execute("UPDATE users SET theme_preference = ? WHERE id = ?", (theme_key, user_id))
    conn.close()


# --- Insert helpers -------------------------------------------------------


def insert_check_in(user_id: int, payload: Dict) -> None:
    conn = _connect()
    with conn:
        conn.execute(
            """
            INSERT INTO check_ins (user_id, timestamp, mood, energy, schedule, note_encrypted)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                payload["timestamp"],
                payload["mood"],
                payload["energy"],
                payload["schedule"],
                payload["note_encrypted"],
            ),
        )
    conn.close()


def insert_appointment(user_id: int, payload: Dict) -> None:
    conn = _connect()
    with conn:
        conn.execute(
            """
            INSERT INTO appointments (user_id, title_encrypted, category, provider_encrypted, date, notes_encrypted, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                payload["title_encrypted"],
                payload["category"],
                payload["provider_encrypted"],
                payload["date"],
                payload["notes_encrypted"],
                datetime.utcnow().isoformat(),
            ),
        )
    conn.close()


def insert_symptom(user_id: int, payload: Dict) -> None:
    conn = _connect()
    with conn:
        conn.execute(
            """
            INSERT INTO symptoms (user_id, symptom_encrypted, severity, notes_encrypted, date, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                payload["symptom_encrypted"],
                payload["severity"],
                payload["notes_encrypted"],
                payload["date"],
                datetime.utcnow().isoformat(),
            ),
        )
    conn.close()


def insert_device(user_id: int, label: str, expo_token: str) -> None:
    conn = _connect()
    with conn:
        conn.execute(
            """
            INSERT INTO devices (user_id, label, expo_token, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, label, expo_token, datetime.utcnow().isoformat()),
        )
    conn.close()


# --- Session tokens --------------------------------------------------------


def store_session_token(user_id: int, token_hash: str, encrypted_key: str, expires_at: str) -> None:
    conn = _connect()
    with conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO session_tokens (user_id, token_hash, encrypted_key, expires_at, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, token_hash, encrypted_key, expires_at, datetime.utcnow().isoformat()),
        )
    conn.close()


def fetch_session_token(token_hash: str) -> Optional[sqlite3.Row]:
    conn = _connect()
    row = conn.execute(
        "SELECT * FROM session_tokens WHERE token_hash = ?",
        (token_hash,),
    ).fetchone()
    conn.close()
    return row


def delete_session_token(token_hash: str) -> None:
    conn = _connect()
    with conn:
        conn.execute("DELETE FROM session_tokens WHERE token_hash = ?", (token_hash,))
    conn.close()


def delete_session_tokens_for_user(user_id: int) -> None:
    conn = _connect()
    with conn:
        conn.execute("DELETE FROM session_tokens WHERE user_id = ?", (user_id,))
    conn.close()
