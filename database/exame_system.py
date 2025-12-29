import sqlite3
import argparse
import json
from datetime import datetime
from typing import List, Tuple
import sys
import bcrypt


class ExamSystemDB:
    def __init__(self, db_name: str = "exam_system.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        self.conn.execute("PRAGMA foreign_keys = ON")

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def migrate(self):
        """
        Create all database tables.
        Hanya membuat tabel yang dibutuhkan untuk Tes Kepribadian Holland.
        Tabel Ujian Modern/Sekolah Dihapus.
        """
        print("Running migrations...")
        
        # 1. Users table (General for all users)
        self.cursor.execute("""
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
        """)

        # 2. Student Profiles table (Specific profile info)
        self.cursor.execute("""
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
        """)

        # 3. Questions table (Holland questions)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                holland_type TEXT NOT NULL CHECK (holland_type IN (
                    'Realistic','Investigative','Artistic','Social','Enterprising','Conventional'
                )),
                discrimination REAL DEFAULT 1.0,
                difficulty REAL DEFAULT 0.0,
                guessing REAL DEFAULT 0.2,
                time_limit_seconds INTEGER DEFAULT 60,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self._ensure_column('questions', 'discrimination', 'REAL DEFAULT 1.0')
        self._ensure_column('questions', 'difficulty', 'REAL DEFAULT 0.0')
        self._ensure_column('questions', 'guessing', 'REAL DEFAULT 0.2')
        self._ensure_column('questions', 'time_limit_seconds', 'INTEGER DEFAULT 60')

        # 4. Majors table (Holland major compatibility scores)
        self.cursor.execute("""
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
        """)

        # 5. Student Answers table (Holland answers)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS student_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer INTEGER NOT NULL CHECK(answer BETWEEN 1 AND 5),
                response_time REAL,
                question_order INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions(id) ON DELETE CASCADE,
                UNIQUE(student_id, question_id)
            )
        """)
        self._ensure_column('student_answers', 'response_time', 'REAL')
        self._ensure_column('student_answers', 'question_order', 'INTEGER')

        # 6. Test Results table (Holland final results)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER UNIQUE NOT NULL,
                holland_scores TEXT NOT NULL,
                anp_results TEXT,
                top_3_types TEXT NOT NULL,
                recommended_major TEXT NOT NULL,
                theta REAL,
                theta_se REAL,
                total_items INTEGER,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
            )
        """)
        self._ensure_column('test_results', 'theta', 'REAL')
        self._ensure_column('test_results', 'theta_se', 'REAL')
        self._ensure_column('test_results', 'total_items', 'INTEGER')
        
        # --- BLOK TABEL MODERN/UJIAN SEKOLAH TELAH DIHAPUS ---
        
        # Indexes (Hanya menyisakan indeks untuk tabel Holland/Legacy)
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_profiles_student ON student_profiles(student_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(holland_type)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_answers_student ON student_answers(student_id)")
        # Indeks untuk exams, questions, attempts, answers dihilangkan

        self.conn.commit()
        print("[OK] Migrations completed successfully! (Hanya tabel Tes Holland yang dibuat)")

    def seed_data(self):
        """Seed database with sample data (Hanya data Holland/Legacy)"""
        print("Seeding data...")

        def hash_password(raw: str) -> str:
            return bcrypt.hashpw(raw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        # User and Student Profile seeding
        base_users = [
            {
                'username': 'admin',
                'password': 'admin123',
                'role': 'admin',
                'full_name': 'Administrator',
                'class_name': None,
                'email': None
            },
            {
                'username': 'student1',
                'password': 'student123',
                'role': 'student',
                'full_name': 'John Doe',
                'class_name': 'XII IPA 1',
                'email': 'john.doe@example.com',
                'profile': {
                    'student_id': 'STU001',
                    'first_name': 'John',
                    'last_name': 'Doe',
                    'enrollment_date': '2024-01-15'
                }
            },
            {
                'username': 'student2',
                'password': 'student123',
                'role': 'student',
                'full_name': 'Jane Smith',
                'class_name': 'XII IPA 2',
                'email': 'jane.smith@example.com',
                'profile': {
                    'student_id': 'STU002',
                    'first_name': 'Jane',
                    'last_name': 'Smith',
                    'enrollment_date': '2024-01-16'
                }
            }
        ]

        for entry in base_users:
            hashed_pwd = hash_password(entry['password'])
            self.cursor.execute(
                """
                INSERT OR IGNORE INTO users (username, password, role, full_name, class_name, email)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    entry['username'],
                    hashed_pwd,
                    entry['role'],
                    entry['full_name'],
                    entry['class_name'],
                    entry.get('email')
                )
            )

            if entry['role'] == 'student':
                user_id = self.cursor.execute(
                    "SELECT id FROM users WHERE username = ?",
                    (entry['username'],)
                ).fetchone()[0]

                profile = entry['profile']
                student_code = profile.get('student_id') or f"STU{user_id:04d}"
                self.cursor.execute(
                    """
                    INSERT OR IGNORE INTO student_profiles (user_id, student_id, first_name, last_name, enrollment_date)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        user_id,
                        student_code,
                        profile['first_name'],
                        profile['last_name'],
                        profile['enrollment_date']
                    )
                )

        # Legacy Holland questions
        holland_questions = [
            ("Saya menikmati memperbaiki atau merakit sesuatu", 'Realistic'),
            ("Saya suka memecahkan masalah logika atau matematis", 'Investigative'),
            ("Saya senang membuat karya seni atau musik", 'Artistic'),
            ("Saya menikmati membantu orang lain", 'Social'),
            ("Saya percaya diri memimpin sebuah tim", 'Enterprising'),
            ("Saya rapi dan menyukai hal-hal terstruktur", 'Conventional')
        ]

        existing_questions = self.cursor.execute("SELECT COUNT(*) FROM questions").fetchone()[0]
        if existing_questions == 0:
            self.cursor.executemany(
                "INSERT INTO questions (question_text, holland_type) VALUES (?, ?)",
                holland_questions
            )

        # Majors seed data
        majors_seed = [
            ('Teknik Informatika', 0.7, 0.8, 0.3, 0.4, 0.6, 0.5),
            ('Desain Komunikasi Visual', 0.3, 0.4, 0.9, 0.5, 0.4, 0.3),
            ('Kedokteran', 0.5, 0.8, 0.4, 0.7, 0.4, 0.4)
        ]

        existing_majors = self.cursor.execute("SELECT COUNT(*) FROM majors").fetchone()[0]
        if existing_majors == 0:
            self.cursor.executemany(
                """
                INSERT INTO majors (Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                majors_seed
            )

        # Seed sample Holland answers for student1
        student1_user_id = self.cursor.execute("SELECT id FROM users WHERE username = 'student1'").fetchone()[0]
        question_ids = [row[0] for row in self.cursor.execute("SELECT id FROM questions ORDER BY id LIMIT 6").fetchall()]
        existing_answers = self.cursor.execute("SELECT COUNT(*) FROM student_answers WHERE student_id = ?", (student1_user_id,)).fetchone()[0]

        if existing_answers == 0 and question_ids:
            holland_answers = [
                (student1_user_id, q_id, (idx % 5) + 1)
                for idx, q_id in enumerate(question_ids)
            ]
            self.cursor.executemany(
                "INSERT INTO student_answers (student_id, question_id, answer) VALUES (?, ?, ?)",
                holland_answers
            )

        # Seed sample test result
        existing_result = self.cursor.execute("SELECT COUNT(*) FROM test_results WHERE student_id = ?", (student1_user_id,)).fetchone()[0]
        if existing_result == 0:
            sample_scores = {
                'Realistic': 0.75,
                'Investigative': 0.82,
                'Artistic': 0.45,
                'Social': 0.68,
                'Enterprising': 0.55,
                'Conventional': 0.60
            }
            top_types = ['Investigative', 'Realistic', 'Social']
            anp_payload = {
                'ranked_majors': [
                    ('Teknik Informatika', {'anp_score': 0.42}),
                    ('Kedokteran', {'anp_score': 0.33}),
                    ('Desain Komunikasi Visual', {'anp_score': 0.25})
                ]
            }

            self.cursor.execute(
                """
                INSERT INTO test_results (student_id, top_3_types, recommended_major, holland_scores, anp_results, completed_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    student1_user_id,
                    json.dumps(top_types),
                    'Teknik Informatika',
                    json.dumps(sample_scores),
                    json.dumps(anp_payload),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                )
            )

        # --- BLOK SEEDING DATA UJIAN SEKOLAH DIHAPUS ---

        self.conn.commit()
        print("[OK] Data seeded successfully!")

    def list_students(self):
        """List all students"""
        self.cursor.execute("""
            SELECT sp.student_id, u.full_name, u.username, u.class_name, u.email, sp.enrollment_date
            FROM student_profiles sp
            JOIN users u ON sp.user_id = u.id
            ORDER BY sp.created_at DESC
        """)
        
        results = self.cursor.fetchall()
        print("\n" + "="*140)
        print(f"{'Student ID':<12} {'Name':<30} {'Username':<15} {'Class':<12} {'Email':<30} {'Enrollment':<12}")
        print("="*140)
        
        for row in results:
            student_id, full_name, username, class_name, email, enrollment = row
            print(f"{student_id:<12} {full_name:<30} {username:<15} {class_name or 'N/A':<12} {(email or 'N/A'):<30} {enrollment or 'N/A':<12}")
        
        print(f"\nTotal students: {len(results)}\n")
    
    # --- FUNGSI list_exams, list_questions (untuk exams), list_attempts, list_answers DIHAPUS ---

    def _ensure_column(self, table_name: str, column_name: str, column_def: str):
        try:
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in self.cursor.fetchall()]
            if column_name not in columns:
                self.cursor.execute(
                    f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}"
                )
        except sqlite3.Error as exc:
            raise RuntimeError(f"Failed ensuring column {table_name}.{column_name}: {exc}")


def main():
    parser = argparse.ArgumentParser(description='Exam System Database Manager (Holland-Focus)')
    # Pilihan perintah hanya 'migrate', 'seed', 'list'
    parser.add_argument('command', choices=['migrate', 'seed', 'list'], 
                        help='Command to execute')
    
    # Pilihan --entity hanya 'students' (karena yang lain adalah data Holland yang tidak ditampilkan dalam daftar sederhana)
    parser.add_argument('--entity', choices=['students'],
                        help='Entity to list (only students supported)')
    
    # Menghapus argumen yang tidak lagi relevan
    # parser.add_argument('--exam-code', help='Exam code filter')
    # parser.add_argument('--student-id', help='Student ID filter')
    
    parser.add_argument('--db', default='exam_system.db', help='Database file name')

    args = parser.parse_args()

    db = ExamSystemDB(args.db)
    
    try:
        db.connect()
        
        if args.command == 'migrate':
            db.migrate()
        
        elif args.command == 'seed':
            db.seed_data()
        
        elif args.command == 'list':
            if args.entity != 'students':
                print("Error: --entity must be 'students' for the list command.")
                sys.exit(1)
            
            db.list_students()
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()