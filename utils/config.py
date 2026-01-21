from .auth import check_login
from database.db_manager import DatabaseManager

def connection():
    """Membuat koneksi ke database dan mengembalikan objek koneksi"""
    check_login()
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    return conn