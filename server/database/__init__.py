"""
server/database — Database connection management
"""

import pymysql
import os
from typing import Generator

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "subladder")

# Connection pool (simple implementation)
_connection_pool = []
MAX_POOL_SIZE = 5


def get_connection() -> pymysql.Connection:
    """Get a database connection from pool or create new one."""
    try:
        # Try to get from pool
        if _connection_pool:
            conn = _connection_pool.pop()
            # Verify connection is still alive
            try:
                conn.ping()
                return conn
            except:
                conn.close()
        
        # Create new connection
        return pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            charset="utf8mb4",
            autocommit=False,
        )
    except pymysql.Error as e:
        print(f"❌ Database connection error: {e}")
        raise


def return_connection(conn: pymysql.Connection) -> None:
    """Return connection to pool."""
    if conn and len(_connection_pool) < MAX_POOL_SIZE:
        try:
            conn.rollback()  # Ensure clean state
            _connection_pool.append(conn)
        except:
            conn.close()
    elif conn:
        conn.close()


def get_db() -> Generator:
    """
    FastAPI dependency for database connections.
    Automatically returns connection to pool after use.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        return_connection(conn)


def close_all_connections() -> None:
    """Close all pooled connections. Call on server shutdown."""
    global _connection_pool
    while _connection_pool:
        try:
            conn = _connection_pool.pop()
            conn.close()
        except:
            pass
