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
        """Create all database tables"""
        print("Running migrations...")
        # Users + legacy-compatible tables
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

        # Modern exam tables (namespaced to avoid conflicts with legacy tables)
        self.cursor.execute("""
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
        """)

        self.cursor.execute("""
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
        """)
        self._ensure_column('exam_questions', 'holland_type', 'TEXT')

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS exam_answer_choices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                exam_question_id INTEGER NOT NULL,
                choice_letter TEXT NOT NULL,
                choice_text TEXT NOT NULL,
                is_correct BOOLEAN NOT NULL DEFAULT 0,
                FOREIGN KEY (exam_question_id) REFERENCES exam_questions(id) ON DELETE CASCADE,
                UNIQUE(exam_question_id, choice_letter)
            )
        """)

        self.cursor.execute("""
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
        """)

        self.cursor.execute("""
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
        """)

        # Indexes
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_profiles_student ON student_profiles(student_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_questions_type ON questions(holland_type)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_student_answers_student ON student_answers(student_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_exams_code ON exams(exam_code)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_exam_questions_exam ON exam_questions(exam_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_attempts_student_profile ON exam_attempts(student_profile_id)")
        self.cursor.execute("CREATE INDEX IF NOT EXISTS idx_exam_answers_attempt ON exam_student_answers(attempt_id)")

        self.conn.commit()
        print("✓ Migrations completed successfully!")

    def seed_data(self):
        """Seed database with sample data"""
        print("Seeding data...")

        def hash_password(raw: str) -> str:
            return bcrypt.hashpw(raw.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

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

        # Insert exams
        exams = [
            ('EXAM001', 'Python Programming Basics', 'Introductory Python exam covering fundamentals', 60, 70.0, 100.0, '2024-03-01'),
            ('EXAM002', 'Database Design', 'SQL and database normalization concepts', 90, 75.0, 100.0, '2024-03-15'),
            ('EXAM003', 'Web Development', 'HTML, CSS, and JavaScript fundamentals', 120, 65.0, 150.0, '2024-04-01'),
        ]

        self.cursor.executemany(
            """
            INSERT OR IGNORE INTO exams (exam_code, title, description, duration_minutes, passing_score, total_points, exam_date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            exams
        )

        # Exam questions per exam
        exam_questions_seed = {
            'EXAM001': [
                (1, 'What is the output of print(type([]))?', 'multiple_choice', 10.0, 'Investigative'),
                (2, 'Python is a compiled language.', 'true_false', 10.0, 'Investigative'),
                (3, 'Explain the difference between a list and a tuple in Python.', 'short_answer', 20.0, 'Conventional'),
                (4, 'Which keyword is used to create a function in Python?', 'multiple_choice', 10.0, 'Investigative')
            ]
        }

        for exam_code, exam_questions in exam_questions_seed.items():
            exam_row = self.cursor.execute("SELECT id FROM exams WHERE exam_code = ?", (exam_code,)).fetchone()
            if not exam_row:
                continue
            exam_id = exam_row[0]
            payload = [
                (exam_id, number, text, qtype, points, holland_hint)
                for (number, text, qtype, points, holland_hint) in exam_questions
            ]
            self.cursor.executemany(
                """
                INSERT OR IGNORE INTO exam_questions (exam_id, question_number, question_text, question_type, points, holland_type)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                payload
            )

        # Insert answer choices for MC questions
        exam1_id = self.cursor.execute("SELECT id FROM exams WHERE exam_code = 'EXAM001'").fetchone()[0]
        q1_id = self.cursor.execute(
            "SELECT id FROM exam_questions WHERE exam_id = ? AND question_number = 1",
            (exam1_id,)
        ).fetchone()[0]
        q4_id = self.cursor.execute(
            "SELECT id FROM exam_questions WHERE exam_id = ? AND question_number = 4",
            (exam1_id,)
        ).fetchone()[0]

        choices = [
            (q1_id, 'A', "<class 'list'>", 1),
            (q1_id, 'B', "<class 'array'>", 0),
            (q1_id, 'C', "<class 'dict'>", 0),
            (q1_id, 'D', "<class 'tuple'>", 0),
            (q4_id, 'A', 'func', 0),
            (q4_id, 'B', 'def', 1),
            (q4_id, 'C', 'function', 0),
            (q4_id, 'D', 'define', 0),
        ]

        self.cursor.executemany(
            """
            INSERT OR IGNORE INTO exam_answer_choices (exam_question_id, choice_letter, choice_text, is_correct)
            VALUES (?, ?, ?, ?)
            """,
            choices
        )

        q1_correct_choice = self.cursor.execute(
            "SELECT id FROM exam_answer_choices WHERE exam_question_id = ? AND choice_letter = 'A'",
            (q1_id,)
        ).fetchone()[0]
        q4_correct_choice = self.cursor.execute(
            "SELECT id FROM exam_answer_choices WHERE exam_question_id = ? AND choice_letter = 'B'",
            (q4_id,)
        ).fetchone()[0]

        # Insert exam attempts
        student1_profile_id = self.cursor.execute(
            "SELECT id FROM student_profiles WHERE student_id = 'STU001'"
        ).fetchone()[0]
        student2_profile_id = self.cursor.execute(
            "SELECT id FROM student_profiles WHERE student_id = 'STU002'"
        ).fetchone()[0]

        attempts = [
            (student1_profile_id, exam1_id, 1, '2024-03-01 09:00:00', '2024-03-01 10:00:00', 85.0, 'completed'),
            (student2_profile_id, exam1_id, 1, '2024-03-01 10:00:00', '2024-03-01 11:00:00', 92.0, 'completed'),
        ]

        self.cursor.executemany(
            """
            INSERT OR IGNORE INTO exam_attempts (student_profile_id, exam_id, attempt_number, start_time, end_time, score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            attempts
        )

        # Insert per-question answers for exam attempts
        attempt_rows = self.cursor.execute(
            "SELECT id, student_profile_id FROM exam_attempts WHERE exam_id = ?",
            (exam1_id,)
        ).fetchall()
        for attempt_id, _ in attempt_rows:
            exam_answers = [
                (attempt_id, q1_id, None, q1_correct_choice, 10.0, True),
                (attempt_id, q4_id, None, q4_correct_choice, 10.0, True)
            ]
            self.cursor.executemany(
                """
                INSERT OR IGNORE INTO exam_student_answers (attempt_id, exam_question_id, answer_text, selected_choice_id, points_earned, is_correct)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                exam_answers
            )

        self.conn.commit()
        print("✓ Data seeded successfully!")

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

    def list_exams(self):
        """List all exams"""
        self.cursor.execute("""
            SELECT exam_code, title, duration_minutes, passing_score, total_points, exam_date
            FROM exams
            ORDER BY exam_date
        """)
        
        results = self.cursor.fetchall()
        print("\n" + "="*120)
        print(f"{'Exam Code':<12} {'Title':<40} {'Duration':<10} {'Pass Score':<12} {'Total Points':<13} {'Date':<12}")
        print("="*120)
        
        for row in results:
            print(f"{row[0]:<12} {row[1]:<40} {row[2]} min    {row[3]:<12} {row[4]:<13} {row[5]:<12}")
        
        print(f"\nTotal exams: {len(results)}\n")

    def list_questions(self, exam_code: str = None):
        """List questions for a specific exam or all exams"""
        if exam_code:
            self.cursor.execute("""
                SELECT e.exam_code, e.title, q.question_number, q.question_text, q.question_type, q.points
                FROM exam_questions q
                JOIN exams e ON q.exam_id = e.id
                WHERE e.exam_code = ?
                ORDER BY q.question_number
            """, (exam_code,))
        else:
            self.cursor.execute("""
                SELECT e.exam_code, e.title, q.question_number, q.question_text, q.question_type, q.points
                FROM exam_questions q
                JOIN exams e ON q.exam_id = e.id
                ORDER BY e.exam_code, q.question_number
            """)
        
        results = self.cursor.fetchall()
        print("\n" + "="*150)
        print(f"{'Exam':<12} {'Q#':<5} {'Question Text':<70} {'Type':<20} {'Points':<8}")
        print("="*150)
        
        for row in results:
            question_text = row[3][:67] + "..." if len(row[3]) > 70 else row[3]
            print(f"{row[0]:<12} {row[2]:<5} {question_text:<70} {row[4]:<20} {row[5]:<8}")
        
        print(f"\nTotal questions: {len(results)}\n")

    def list_attempts(self, student_id: str = None):
        """List exam attempts"""
        if student_id:
            self.cursor.execute("""
                SELECT sp.student_id, u.full_name, e.exam_code, e.title,
                       ea.attempt_number, ea.score, ea.status, ea.start_time
                FROM exam_attempts ea
                JOIN student_profiles sp ON ea.student_profile_id = sp.id
                JOIN users u ON sp.user_id = u.id
                JOIN exams e ON ea.exam_id = e.id
                WHERE sp.student_id = ?
                ORDER BY ea.start_time DESC
            """, (student_id,))
        else:
            self.cursor.execute("""
                SELECT sp.student_id, u.full_name, e.exam_code, e.title,
                       ea.attempt_number, ea.score, ea.status, ea.start_time
                FROM exam_attempts ea
                JOIN student_profiles sp ON ea.student_profile_id = sp.id
                JOIN users u ON sp.user_id = u.id
                JOIN exams e ON ea.exam_id = e.id
                ORDER BY ea.start_time DESC
            """)

        results = self.cursor.fetchall()
        print("\n" + "="*140)
        print(f"{'Student':<12} {'Name':<25} {'Exam':<12} {'Title':<30} {'Att#':<5} {'Score':<8} {'Status':<12} {'Date':<15}")
        print("="*140)

        for row in results:
            student_code, full_name, exam_code, title, attempt_no, score_value, status, start_time = row
            score = f"{score_value:.1f}" if score_value is not None else "N/A"
            print(f"{student_code:<12} {full_name:<25} {exam_code:<12} {title:<30} {attempt_no:<5} {score:<8} {status:<12} {start_time:<15}")

        print(f"\nTotal attempts: {len(results)}\n")

    def list_answers(self, student_id: str, exam_code: str):
        """List answers for a specific student and exam"""
        self.cursor.execute("""
            SELECT q.question_number, q.question_text, q.question_type, q.points,
                   esa.answer_text, ac.choice_letter, ac.choice_text,
                   esa.points_earned, esa.is_correct
            FROM exam_student_answers esa
            JOIN exam_attempts ea ON esa.attempt_id = ea.id
            JOIN student_profiles sp ON ea.student_profile_id = sp.id
            JOIN exams e ON ea.exam_id = e.id
            JOIN exam_questions q ON esa.exam_question_id = q.id
            LEFT JOIN exam_answer_choices ac ON esa.selected_choice_id = ac.id
            WHERE sp.student_id = ? AND e.exam_code = ?
            ORDER BY q.question_number
        """, (student_id, exam_code))
        
        results = self.cursor.fetchall()
        print(f"\n{'='*130}")
        print(f"Answers for Student: {student_id}, Exam: {exam_code}")
        print(f"{'='*130}\n")
        
        for row in results:
            print(f"Q{row[0]}: {row[1]}")
            print(f"Type: {row[2]} | Points: {row[3]}")
            
            if row[4]:  # answer_text
                print(f"Answer: {row[4]}")
            elif row[5]:  # choice_letter
                print(f"Selected: {row[5]}) {row[6]}")
            
            if row[7] is not None:
                correct_mark = "✓" if row[8] else "✗"
                print(f"Score: {row[7]}/{row[3]} {correct_mark}")
            print()
        
        print(f"Total answers: {len(results)}\n")

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
    parser = argparse.ArgumentParser(description='Exam System Database Manager')
    parser.add_argument('command', choices=['migrate', 'seed', 'list'], 
                       help='Command to execute')
    parser.add_argument('--entity', choices=['students', 'exams', 'questions', 'attempts', 'answers'],
                       help='Entity to list (for list command)')
    parser.add_argument('--exam-code', help='Exam code filter')
    parser.add_argument('--student-id', help='Student ID filter')
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
            if not args.entity:
                print("Error: --entity is required for list command")
                sys.exit(1)
            
            if args.entity == 'students':
                db.list_students()
            elif args.entity == 'exams':
                db.list_exams()
            elif args.entity == 'questions':
                db.list_questions(args.exam_code)
            elif args.entity == 'attempts':
                db.list_attempts(args.student_id)
            elif args.entity == 'answers':
                if not args.student_id or not args.exam_code:
                    print("Error: --student-id and --exam-code required for answers")
                    sys.exit(1)
                db.list_answers(args.student_id, args.exam_code)
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
    
    finally:
        db.close()


if __name__ == "__main__":
    main()



