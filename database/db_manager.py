import sqlite3
from datetime import datetime
import bcrypt

from database.exame_system import ExamSystemDB


class DatabaseManager:
    _schema_initialized = False
    _defaults_seeded = False

    def __init__(self, db_path="exam_system.db"):
        self.db_path = db_path
        print("dbManager:", db_path)
        self._ensure_schema()
        self._ensure_default_records()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # ==============================
    #  INISIALISASI DATABASE
    # ==============================
    def init_database(self):
        self._ensure_schema()
        self._ensure_default_records()
    

    # ==============================
    #  INSERT DEFAULT ADMIN & STUDENT
    # ==============================
    def insert_default_data(self, cursor):
        # ---------- ADMIN ----------
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]

        if admin_count == 0:
            admin_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt()).decode()

            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password, role, full_name)
                VALUES (?, ?, ?, ?)
            ''', ("admin", admin_password, "admin", "Administrator"))


    # ==============================
    #  SCHEMA MANAGEMENT
    # ==============================
    def _ensure_schema(self):
        if DatabaseManager._schema_initialized:
            return

        conn = self.get_connection()
        exam_db = ExamSystemDB(conn)
        exam_db.connect()
        try:
            exam_db.migrate()
        finally:
            exam_db.close()

        DatabaseManager._schema_initialized = True

    def _ensure_default_records(self):
        if DatabaseManager._defaults_seeded:
            return

        conn = self.get_connection()
        cursor = conn.cursor()
        self.insert_default_data(cursor)
        conn.commit()
        conn.close()

        DatabaseManager._defaults_seeded = True
