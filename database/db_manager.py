import sqlite3
import bcrypt
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path="talent_test_baruku.db"):
        self.db_path = db_path
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        """Inisialisasi database dan tabel"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Tabel users
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('admin', 'student')),
                full_name TEXT NOT NULL,
                class_name TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel questions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                holland_type TEXT NOT NULL CHECK (holland_type IN ('Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Tabel student_answers
        cursor.execute('''
           CREATE TABLE IF NOT EXISTS student_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                result_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer INTEGER NOT NULL CHECK (answer BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (result_id) REFERENCES test_results (id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions (id),
                UNIQUE(result_id, question_id)
            )
        ''')
        
        # Tabel alternatives (college majors with RIASEC weights)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS alternatives (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                major_name TEXT UNIQUE NOT NULL,
                realistic REAL NOT NULL,
                investigative REAL NOT NULL,
                artistic REAL NOT NULL,
                social REAL NOT NULL,
                enterprising REAL NOT NULL,
                conventional REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Tabel criteria (top 3 RIASEC scores from student results)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS criteria (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                result_id INTEGER NOT NULL,
                riasec_type TEXT NOT NULL,
                score REAL NOT NULL,
                FOREIGN KEY (result_id) REFERENCES test_results (id)
            )
        ''')

        # Tabel test_results (history of student tests)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                holland_scores TEXT NOT NULL,
                anp_results TEXT,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users (id)
            )
        ''')
        
        conn.commit()
        
        # Insert default admin dan sample data
        self.insert_default_data(cursor)
        conn.commit()
        conn.close()
    
    def insert_default_data(self, cursor):
        """Insert data default untuk testing"""
        
        # Cek apakah admin sudah ada
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        admin_count = cursor.fetchone()[0]
        
        if admin_count == 0:
            # Hash password untuk admin
            admin_password = bcrypt.hashpw("admin123".encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (username, password, role, full_name)
                VALUES (?, ?, ?, ?)
            ''', ("admin", admin_password, "admin", "Administrator"))
        
        # Cek apakah questions sudah ada
        cursor.execute("SELECT COUNT(*) FROM questions")
        question_count = cursor.fetchone()[0]
        
        if question_count == 0:
            # Sample questions untuk setiap Holland type
            sample_questions = [
                ("Saya suka bekerja dengan tangan dan alat-alat", "Realistic"),
                ("Saya senang memperbaiki barang-barang yang rusak", "Realistic"),
                ("Saya tertarik dengan kegiatan outdoor dan olahraga", "Realistic"),
                
                ("Saya suka melakukan penelitian dan eksperimen", "Investigative"),
                ("Saya senang memecahkan masalah yang kompleks", "Investigative"),
                ("Saya tertarik dengan ilmu pengetahuan dan teknologi", "Investigative"),
                
                ("Saya suka menggambar, melukis, atau berkarya seni", "Artistic"),
                ("Saya senang menulis cerita atau puisi", "Artistic"),
                ("Saya tertarik dengan musik dan pertunjukan", "Artistic"),
                
                ("Saya suka membantu orang lain menyelesaikan masalah", "Social"),
                ("Saya senang bekerja dalam tim dan berkolaborasi", "Social"),
                ("Saya tertarik dengan kegiatan sosial dan kemanusiaan", "Social"),
                
                ("Saya suka memimpin dan mengorganisir kegiatan", "Enterprising"),
                ("Saya senang berbicara di depan umum", "Enterprising"),
                ("Saya tertarik dengan bisnis dan kewirausahaan", "Enterprising"),
                
                ("Saya suka bekerja dengan data dan angka", "Conventional"),
                ("Saya senang mengatur dan mengelola dokumen", "Conventional"),
                ("Saya tertarik dengan pekerjaan administrasi", "Conventional"),
            ]
            
            cursor.executemany('''
                INSERT INTO questions (question_text, holland_type)
                VALUES (?, ?)
            ''', sample_questions)
        
        # Sample student
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        student_count = cursor.fetchone()[0]
        
        if student_count == 0:
            student_password = bcrypt.hashpw("student123".encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (username, password, role, full_name, class_name)
                VALUES (?, ?, ?, ?, ?)
            ''', ("student1", student_password, "student", "Siswa Contoh", "XII IPA 1"))