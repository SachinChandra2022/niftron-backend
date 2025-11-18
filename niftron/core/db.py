# niftron/core/db.py

import psycopg2
from .config import settings
from contextlib import contextmanager

@contextmanager
def get_db_connection():
    """
    Provides a database connection using a context manager.
    Ensures the connection is closed after use.
    """
    conn = None
    try:
        conn = psycopg2.connect(settings.DATABASE_URL)
        yield conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise
    finally:
        if conn:
            conn.close()

