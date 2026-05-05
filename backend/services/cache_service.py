import sqlite3
import hashlib
import json
import os
import re
from datetime import datetime, timedelta
from typing import Optional

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'cache.db')

# Cache expiry in days — results older than this are ignored
CACHE_EXPIRY_DAYS = 90


def init_cache_db():
    """
    Initialise the SQLite database and create the cache table if it
    does not already exist. Call this once on app startup.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS translation_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_hash TEXT UNIQUE NOT NULL,
            document_name TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            last_accessed TEXT NOT NULL,
            hit_count INTEGER DEFAULT 0
        )
    ''')
    # Index on document_hash for fast lookups
    cursor.execute('''
        CREATE INDEX IF NOT EXISTS idx_document_hash
        ON translation_cache (document_hash)
    ''')
    conn.commit()
    conn.close()


def normalise_document(text: str) -> str:
    """
    Normalise document text before hashing.
    This ensures minor formatting differences in the same document
    (extra spaces, different line endings) produce the same hash.
    """
    # Convert to lowercase
    text = text.lower()
    # Normalise all whitespace (tabs, multiple spaces, newlines) to single space
    text = re.sub(r'\s+', ' ', text)
    # Strip leading and trailing whitespace
    text = text.strip()
    return text


def generate_hash(document_text: str) -> str:
    """
    Generate a SHA-256 hash of the normalised document text.
    Returns a hex string.
    """
    normalised = normalise_document(document_text)
    hash_value = hashlib.sha256(normalised.encode('utf-8')).hexdigest()
    return hash_value


def get_cached_result(document_hash: str) -> Optional[dict]:
    """
    Look up a translation result by document hash.
    Returns the parsed result dict if found and not expired.
    Returns None if not found or expired.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT result_json, created_at, hit_count
        FROM translation_cache
        WHERE document_hash = ?
    ''', (document_hash,))

    row = cursor.fetchone()

    if row is None:
        conn.close()
        return None

    result_json, created_at_str, hit_count = row

    # Check if cache entry has expired
    created_at = datetime.fromisoformat(created_at_str)
    if datetime.utcnow() - created_at > timedelta(days=CACHE_EXPIRY_DAYS):
        # Expired — delete the entry and return None
        cursor.execute(
            'DELETE FROM translation_cache WHERE document_hash = ?',
            (document_hash,)
        )
        conn.commit()
        conn.close()
        return None

    # Update last_accessed and increment hit_count
    cursor.execute('''
        UPDATE translation_cache
        SET last_accessed = ?, hit_count = hit_count + 1
        WHERE document_hash = ?
    ''', (datetime.utcnow().isoformat(), document_hash))
    conn.commit()
    conn.close()
    return json.loads(result_json)


def store_result(document_hash: str, document_name: str, result: dict):
    """
    Store a translation result in the cache.
    If an entry with the same hash already exists, update it.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    now = datetime.utcnow().isoformat()

    cursor.execute('''
        INSERT INTO translation_cache
            (document_hash, document_name, result_json, created_at, last_accessed, hit_count)
        VALUES (?, ?, ?, ?, ?, 0)
        ON CONFLICT(document_hash) DO UPDATE SET
            result_json = excluded.result_json,
            document_name = excluded.document_name,
            last_accessed = excluded.last_accessed
    ''', (
        document_hash,
        document_name,
        json.dumps(result),
        now,
        now
    ))
    conn.commit()
    conn.close()


def cleanup_expired_entries():
    """
    Delete all cache entries older than CACHE_EXPIRY_DAYS.
    Call this from a scheduled task or manually.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    expiry_date = (datetime.utcnow() - timedelta(days=CACHE_EXPIRY_DAYS)).isoformat()
    cursor.execute(
        'DELETE FROM translation_cache WHERE created_at < ?',
        (expiry_date,)
    )
    deleted_count = cursor.rowcount
    conn.commit()
    conn.close()
    return deleted_count


def get_cache_stats() -> dict:
    """
    Return basic cache statistics. Useful for monitoring.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*), SUM(hit_count) FROM translation_cache')
    row = cursor.fetchone()
    conn.close()
    return {
        "total_entries": row[0] or 0,
        "total_hits": row[1] or 0
    }
