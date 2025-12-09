import sqlite3
from datetime import datetime
import bcrypt

from database.exame_system import ExamSystemDB


class DatabaseManager:
    _schema_initialized = False
    _defaults_seeded = False

    def __init__(self, db_path="exam_system.db"):
        self.db_path = db_path
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

        # ---------- SAMPLE STUDENT ----------
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        student_count = cursor.fetchone()[0]

        if student_count == 0:
            student_password = bcrypt.hashpw("student123".encode('utf-8'), bcrypt.gensalt()).decode()

            cursor.execute('''
                INSERT OR IGNORE INTO users (username, password, role, full_name, class_name)
                VALUES (?, ?, ?, ?, ?)
            ''', ("student1", student_password, "student", "Siswa Contoh", "XII IPA 1"))

            cursor.execute("SELECT id, full_name, class_name FROM users WHERE username = ?", ("student1",))
            row = cursor.fetchone()
            if row:
                self.ensure_student_profile(cursor, row[0], row[1], row[2])

        # Backfill profiles for any other students (if seeded elsewhere)
        self.backfill_student_profiles(cursor)

    # ==============================
    #  SCHEMA MANAGEMENT
    # ==============================
    def _ensure_schema(self):
        if DatabaseManager._schema_initialized:
            return

        exam_db = ExamSystemDB(self.db_path)
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

    # ==============================
    #  HELPER METHODS
    # ==============================
    def ensure_student_profile(self, cursor, user_id, full_name, class_name=None):
        if not user_id:
            return

        cursor.execute("SELECT 1 FROM student_profiles WHERE user_id = ?", (user_id,))
        if cursor.fetchone():
            return

        first_name, last_name = self._split_full_name(full_name)
        student_code = f"STU{user_id:04d}"
        enrollment_date = datetime.now().date().isoformat()

        cursor.execute('''
            INSERT OR IGNORE INTO student_profiles (user_id, student_id, first_name, last_name, enrollment_date)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, student_code, first_name, last_name, enrollment_date))

    def update_student_profile(self, cursor, user_id, full_name):
        first_name, last_name = self._split_full_name(full_name)
        cursor.execute('''
            UPDATE student_profiles
            SET first_name = ?, last_name = ?
            WHERE user_id = ?
        ''', (first_name, last_name, user_id))

    def backfill_student_profiles(self, cursor):
        cursor.execute('''
            SELECT id, full_name, class_name
            FROM users
            WHERE role = 'student' AND id NOT IN (
                SELECT user_id FROM student_profiles
            )
        ''')

        for user_id, full_name, class_name in cursor.fetchall():
            self.ensure_student_profile(cursor, user_id, full_name, class_name)

    @staticmethod
    def _split_full_name(full_name: str):
        if not full_name:
            return "Siswa", ""
        parts = full_name.strip().split()
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], " ".join(parts[1:])
