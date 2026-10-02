from contextlib import contextmanager
from psycopg_pool import ConnectionPool

from app.config import DATABASE_URL

# Create a connection pool
pool = ConnectionPool(conninfo=DATABASE_URL, min_size=1, max_size=10)

# Context manager to get a connection from the pool
@contextmanager
def get_connection():
    with pool.connection() as conn:
        yield conn