import sqlite3
import pandas as pd
import bcrypt
from datetime import datetime


class DatabaseManager:
    def __init__(self, db_path="talent_test.db"):
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
                created_at TIMESTAMP DEFAULT (datetime("now", "+8 hours"))
            )
        ''')
        
        # Tabel questions
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                holland_type TEXT NOT NULL CHECK (holland_type IN ('Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional')),
                created_at TIMESTAMP DEFAULT (datetime("now", "+8 hours"))
            )
        ''')
        # Tabel majors (alternatif jurusan)
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

        
        # Tabel student_answers
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer INTEGER NOT NULL CHECK (answer BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT (datetime("now", "+8 hours")),
                FOREIGN KEY (student_id) REFERENCES users (id),
                FOREIGN KEY (question_id) REFERENCES questions (id),
                UNIQUE(student_id, question_id)
            )
        ''')
        
        # Tabel test_results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                top_3_types TEXT NOT NULL,
                recommended_major TEXT NOT NULL,
                holland_scores TEXT NOT NULL,
                anp_results TEXT,
                completed_at TIMESTAMP DEFAULT (datetime("now", "+8 hours")),
                FOREIGN KEY (student_id) REFERENCES users (id),
                UNIQUE(student_id)
            )
        ''')
        
        # Add ANP column to existing table if it doesn't exist
        try:
            cursor.execute('ALTER TABLE test_results ADD COLUMN anp_results TEXT')
        except:
            # Column already exists or other error, continue
            pass
        
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