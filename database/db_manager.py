import sqlite3
from datetime import datetime
import bcrypt


class DatabaseManager:
    def __init__(self, db_path="exam_system.db"):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)

    # ==============================
    #  INISIALISASI DATABASE
    # ==============================
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        self._create_core_tables(cursor)
        self._create_exam_tables(cursor)
        self.backfill_student_profiles(cursor)

        # Insert admin & sample student
        self.insert_default_data(cursor)

        conn.commit()
        conn.close()
    

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
    #  HELPER METHODS
    # ==============================
    def _create_core_tables(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'student')),
                full_name TEXT NOT NULL,
                class_name TEXT,
                email TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        self._ensure_column(cursor, "users", "email", "TEXT")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email_unique ON users(email)")

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                student_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                enrollment_date DATE DEFAULT CURRENT_DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                holland_type TEXT NOT NULL CHECK (holland_type IN 
                    ('Realistic','Investigative','Artistic','Social','Enterprising','Conventional')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS majors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                Major TEXT UNIQUE NOT NULL,
                Realistic REAL DEFAULT 0,
                Investigative REAL DEFAULT 0,
                Artistic REAL DEFAULT 0,
                Social REAL DEFAULT 0,
                Enterprising REAL DEFAULT 0,
                Conventional REAL DEFAULT 0
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer INTEGER NOT NULL CHECK (answer BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
                UNIQUE(student_id, question_id)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER UNIQUE NOT NULL,
                holland_scores TEXT NOT NULL,
                anp_results TEXT,
                top_3_types TEXT NOT NULL,
                recommended_major TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_profiles_student ON student_profiles(student_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(holland_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_answers_student ON student_answers(student_id)")

    def _create_exam_tables(self, cursor):
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exams (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_code TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                duration_minutes INTEGER NOT NULL,
                passing_score REAL NOT NULL,
                total_points REAL NOT NULL,
                exam_date DATE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_id INTEGER NOT NULL,
                question_number INTEGER NOT NULL,
                question_text TEXT NOT NULL,
                question_type TEXT CHECK(question_type IN ('multiple_choice', 'true_false', 'short_answer', 'essay')) NOT NULL,
                points REAL NOT NULL,
                holland_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
                UNIQUE(exam_id, question_number)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_answer_choices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_question_id INTEGER NOT NULL,
                choice_letter TEXT NOT NULL,
                choice_text TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (exam_question_id) REFERENCES exam_questions(id) ON DELETE CASCADE,
                UNIQUE(exam_question_id, choice_letter)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_attempts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_profile_id INTEGER NOT NULL,
                exam_id INTEGER NOT NULL,
                attempt_number INTEGER NOT NULL,
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                score REAL,
                status TEXT CHECK(status IN ('in_progress', 'completed', 'abandoned')) DEFAULT 'in_progress',
                FOREIGN KEY (student_profile_id) REFERENCES student_profiles(id) ON DELETE CASCADE,
                FOREIGN KEY (exam_id) REFERENCES exams(id) ON DELETE CASCADE,
                UNIQUE(student_profile_id, exam_id, attempt_number)
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_student_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attempt_id INTEGER NOT NULL,
                exam_question_id INTEGER NOT NULL,
                answer_text TEXT,
                selected_choice_id INTEGER,
                points_earned REAL,
                is_correct BOOLEAN,
                answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (attempt_id) REFERENCES exam_attempts(id) ON DELETE CASCADE,
                FOREIGN KEY (exam_question_id) REFERENCES exam_questions(id) ON DELETE CASCADE,
                FOREIGN KEY (selected_choice_id) REFERENCES exam_answer_choices(id),
                UNIQUE(attempt_id, exam_question_id)
            )
        ''')

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exams_code ON exams(exam_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exam_questions_exam ON exam_questions(exam_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exam_attempts_student ON exam_attempts(student_profile_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_exam_answers_attempt ON exam_student_answers(attempt_id)")

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

    @staticmethod
    def _ensure_column(cursor, table_name: str, column_name: str, column_def: str):
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row[1] for row in cursor.fetchall()]
        if column_name not in columns:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")
