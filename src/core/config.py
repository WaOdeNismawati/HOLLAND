from contextlib import contextmanager

from src.core.auth import check_login
from src.infrastructure.database.db_manager import DatabaseManager


def connection(*, require_session: bool = True):
    """Mengembalikan objek koneksi database (pemanggil wajib menutup)."""
    if require_session:
        check_login()
    db_manager = DatabaseManager()
    return db_manager.get_connection()


@contextmanager
def connection_context(*, require_session: bool = True):
    """Context manager untuk memastikan koneksi tertutup otomatis."""
    conn = connection(require_session=require_session)
    try:
        yield conn
    finally:
        conn.close()


# Backward compatibility alias
managed_connection = connection_context