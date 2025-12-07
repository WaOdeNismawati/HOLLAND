import sqlite3
import bcrypt


class DatabaseManager:
    def __init__(self, db_path="talent_test.db"):
        self.db_path = db_path

    def get_connection(self):
        return sqlite3.connect(self.db_path, timeout=10, check_same_thread=False)
  
    # ==============================
    #  INISIALISASI DATABASE
    # ==============================
    def init_database(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # ---------- USERS ----------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'student')),
                full_name TEXT NOT NULL,
                class_name TEXT,
                created_at TIMESTAMP DEFAULT (datetime("now", "+8 hours"))
            )
        ''')

        # ---------- QUESTIONS ----------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                holland_type TEXT NOT NULL CHECK (holland_type IN 
                    ('Realistic','Investigative','Artistic','Social','Enterprising','Conventional')),
                created_at TIMESTAMP DEFAULT (datetime("now", "+8 hours"))
            )
        ''')

        # ---------- MAJORS ----------
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

        # ---------- STUDENT ANSWERS ----------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer INTEGER NOT NULL CHECK (answer BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT (datetime("now", "+8 hours")),
                FOREIGN KEY (student_id) REFERENCES users(id),
                FOREIGN KEY (question_id) REFERENCES questions(id),
                UNIQUE(student_id, question_id)
            )
        ''')

        # ---------- TEST RESULTS ----------
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER UNIQUE NOT NULL,
                holland_scores TEXT NOT NULL,
                anp_results TEXT,
                top_3_types TEXT NOT NULL,
                recommended_major TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT (datetime("now", "+8 hours")),
                FOREIGN KEY (student_id) REFERENCES users(id)
            )
        ''')

        conn.commit()

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