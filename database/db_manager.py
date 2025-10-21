import sqlite3
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
        
        # Tabel student_answers - Reverted to simple, non-history version
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS student_answers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER NOT NULL,
                question_id INTEGER NOT NULL,
                answer INTEGER NOT NULL CHECK (answer BETWEEN 1 AND 5),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE,
                FOREIGN KEY (question_id) REFERENCES questions (id),
                UNIQUE(student_id, question_id)
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

        # Tabel test_results - Reverted to one result per student
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id INTEGER UNIQUE NOT NULL,
                holland_scores TEXT NOT NULL,
                anp_results TEXT,
                top_3_types TEXT NOT NULL,
                recommended_major TEXT NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (student_id) REFERENCES users (id) ON DELETE CASCADE
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
            cursor.executemany("INSERT INTO questions (question_text, holland_type) VALUES (?, ?)", sample_questions)
        
        # Cek apakah alternatives sudah ada
        cursor.execute("SELECT COUNT(*) FROM alternatives")
        if cursor.fetchone()[0] == 0:
            sample_alternatives = [
                ('Teknik Mesin', 0.9, 0.8, 0.2, 0.3, 0.4, 0.7), ('Teknik Informatika', 0.6, 0.9, 0.5, 0.4, 0.6, 0.8),
                ('Teknik Elektro', 0.8, 0.9, 0.3, 0.3, 0.5, 0.7), ('Teknik Sipil', 0.9, 0.7, 0.4, 0.5, 0.6, 0.8),
                ('Arsitektur', 0.7, 0.6, 0.9, 0.4, 0.5, 0.6), ('Teknik Industri', 0.6, 0.8, 0.3, 0.6, 0.8, 0.9),
                ('Sistem Informasi', 0.4, 0.8, 0.5, 0.6, 0.7, 0.9), ('Teknik Kimia', 0.7, 0.9, 0.2, 0.4, 0.5, 0.8),
                ('Teknik Lingkungan', 0.7, 0.8, 0.4, 0.6, 0.5, 0.7), ('Teknik Nuklir', 0.8, 0.9, 0.1, 0.2, 0.4, 0.8),
                ('Kedokteran', 0.5, 0.9, 0.3, 0.9, 0.4, 0.7), ('Farmasi', 0.4, 0.8, 0.2, 0.7, 0.5, 0.9),
                ('Keperawatan', 0.5, 0.6, 0.3, 0.9, 0.4, 0.8), ('Kesehatan Masyarakat', 0.3, 0.7, 0.4, 0.9, 0.6, 0.7),
                ('Gizi', 0.4, 0.8, 0.3, 0.8, 0.5, 0.8), ('Kedokteran Gigi', 0.6, 0.8, 0.4, 0.8, 0.6, 0.7),
                ('Fisioterapi', 0.6, 0.7, 0.2, 0.9, 0.5, 0.6), ('Manajemen', 0.3, 0.5, 0.4, 0.8, 0.9, 0.8),
                ('Akuntansi', 0.2, 0.6, 0.2, 0.5, 0.6, 0.9), ('Ekonomi', 0.3, 0.8, 0.3, 0.6, 0.8, 0.8),
                ('Administrasi Bisnis', 0.3, 0.5, 0.4, 0.7, 0.9, 0.9), ('Keuangan dan Perbankan', 0.2, 0.7, 0.2, 0.6, 0.8, 0.9),
                ('Pemasaran', 0.3, 0.4, 0.6, 0.8, 0.9, 0.7), ('Psikologi', 0.2, 0.8, 0.5, 0.9, 0.4, 0.6),
                ('Pendidikan', 0.3, 0.6, 0.7, 0.9, 0.5, 0.7), ('Sosiologi', 0.2, 0.8, 0.5, 0.9, 0.4, 0.5),
                ('Hubungan Internasional', 0.2, 0.7, 0.4, 0.8, 0.8, 0.6), ('Ilmu Komunikasi', 0.3, 0.5, 0.8, 0.9, 0.7, 0.5),
                ('Ilmu Politik', 0.2, 0.8, 0.5, 0.8, 0.9, 0.6), ('Hukum', 0.2, 0.8, 0.4, 0.8, 0.8, 0.8),
                ('Desain Komunikasi Visual', 0.4, 0.4, 0.9, 0.6, 0.6, 0.4), ('Seni Rupa', 0.6, 0.3, 0.9, 0.4, 0.4, 0.3),
                ('Desain Interior', 0.7, 0.4, 0.9, 0.5, 0.5, 0.4), ('Musik', 0.4, 0.3, 0.9, 0.6, 0.5, 0.3),
                ('Film dan Televisi', 0.5, 0.4, 0.9, 0.7, 0.7, 0.4), ('Sastra Indonesia', 0.2, 0.6, 0.9, 0.7, 0.4, 0.4),
                ('Sastra Inggris', 0.2, 0.6, 0.9, 0.8, 0.5, 0.4), ('Matematika', 0.2, 0.9, 0.3, 0.3, 0.3, 0.8),
                ('Fisika', 0.5, 0.9, 0.4, 0.3, 0.3, 0.7), ('Kimia', 0.6, 0.9, 0.2, 0.3, 0.3, 0.7),
                ('Biologi', 0.4, 0.9, 0.3, 0.4, 0.3, 0.6), ('Statistika', 0.2, 0.9, 0.3, 0.4, 0.5, 0.9),
                ('Geografi', 0.7, 0.8, 0.4, 0.5, 0.4, 0.6), ('Astronomi', 0.3, 0.9, 0.2, 0.2, 0.3, 0.7),
                ('Agribisnis', 0.6, 0.6, 0.3, 0.7, 0.8, 0.8), ('Kehutanan', 0.8, 0.7, 0.4, 0.5, 0.5, 0.6),
                ('Oseanografi', 0.7, 0.8, 0.3, 0.4, 0.4, 0.5), ('Studi Umum (General)', 0.167, 0.167, 0.167, 0.167, 0.167, 0.167),
                ('Cybersecurity', 0.5, 0.9, 0.3, 0.3, 0.6, 0.8), ('Data Science', 0.3, 0.9, 0.4, 0.5, 0.6, 0.8),
                ('Game Development', 0.6, 0.7, 0.9, 0.4, 0.6, 0.5), ('Cloud Computing', 0.5, 0.8, 0.2, 0.4, 0.6, 0.9),
                ('AI and Machine Learning', 0.4, 0.9, 0.4, 0.4, 0.5, 0.8), ('Kesehatan Publik', 0.3, 0.7, 0.3, 0.9, 0.6, 0.7),
                ('Kedokteran Hewan', 0.7, 0.8, 0.2, 0.8, 0.5, 0.6), ('Optometri', 0.6, 0.8, 0.3, 0.8, 0.6, 0.7),
                ('Radiografi', 0.7, 0.7, 0.2, 0.8, 0.4, 0.8), ('Terapi Wicara', 0.3, 0.7, 0.4, 0.9, 0.5, 0.7),
                ('Manajemen Sumber Daya Manusia', 0.2, 0.5, 0.4, 0.8, 0.8, 0.8), ('Bisnis Internasional', 0.3, 0.6, 0.4, 0.7, 0.9, 0.7),
                ('Logistik & Rantai Pasok', 0.6, 0.6, 0.2, 0.5, 0.8, 0.9), ('Kewirausahaan', 0.4, 0.5, 0.6, 0.7, 0.9, 0.6),
                ('Real Estate', 0.5, 0.4, 0.3, 0.7, 0.9, 0.8), ('Antropologi', 0.4, 0.8, 0.5, 0.8, 0.4, 0.5),
                ('Kriminologi', 0.4, 0.8, 0.3, 0.8, 0.6, 0.7), ('Ilmu Perpustakaan', 0.2, 0.6, 0.5, 0.7, 0.4, 0.9),
                ('Perencanaan Kota', 0.6, 0.7, 0.6, 0.7, 0.6, 0.8), ('Pekerjaan Sosial', 0.2, 0.6, 0.4, 0.9, 0.5, 0.7),
                ('Penulisan Kreatif', 0.1, 0.5, 0.9, 0.6, 0.4, 0.4), ('Seni Teater', 0.3, 0.4, 0.9, 0.8, 0.7, 0.3),
                ('Filsafat', 0.1, 0.9, 0.6, 0.6, 0.4, 0.5), ('Sejarah', 0.2, 0.8, 0.5, 0.6, 0.4, 0.7),
                ('Linguistik', 0.2, 0.8, 0.6, 0.7, 0.4, 0.6), ('Ilmu Lingkungan', 0.7, 0.9, 0.4, 0.6, 0.5, 0.6),
                ('Geologi', 0.8, 0.8, 0.2, 0.4, 0.4, 0.6), ('Biologi Laut', 0.7, 0.8, 0.4, 0.5, 0.4, 0.5),
                ('Ilmu Saraf (Neuroscience)', 0.4, 0.9, 0.3, 0.7, 0.4, 0.6), ('Astrofisika', 0.4, 0.9, 0.2, 0.2, 0.3, 0.7),
                ('Pendidikan Anak Usia Dini', 0.3, 0.5, 0.6, 0.9, 0.5, 0.7), ('Pendidikan Luar Biasa', 0.3, 0.6, 0.5, 0.9, 0.5, 0.8),
                ('Pendidikan Jasmani', 0.7, 0.5, 0.3, 0.8, 0.6, 0.6), ('Kepemimpinan Pendidikan', 0.2, 0.6, 0.4, 0.8, 0.8, 0.8),
                ('Kurikulum & Pengajaran', 0.2, 0.7, 0.5, 0.8, 0.5, 0.8), ('Teknik Dirgantara', 0.9, 0.9, 0.3, 0.2, 0.4, 0.7),
                ('Teknik Biomedis', 0.7, 0.9, 0.3, 0.6, 0.5, 0.7), ('Teknik Perminyakan', 0.9, 0.8, 0.1, 0.3, 0.6, 0.7),
                ('Teknik Pertanian', 0.8, 0.7, 0.2, 0.5, 0.6, 0.7), ('Teknik Kelautan', 0.9, 0.8, 0.2, 0.4, 0.5, 0.6),
                ('Pariwisata dan Perhotelan', 0.4, 0.4, 0.5, 0.8, 0.8, 0.8), ('Desain Mode', 0.5, 0.3, 0.9, 0.6, 0.8, 0.5),
                ('Animasi', 0.5, 0.5, 0.9, 0.4, 0.5, 0.5), ('Seni Kuliner', 0.6, 0.3, 0.7, 0.7, 0.7, 0.6),
                ('Jurnalistik', 0.3, 0.7, 0.7, 0.8, 0.8, 0.6)
            ]
            cursor.executemany("INSERT INTO alternatives (major_name, realistic, investigative, artistic, social, enterprising, conventional) VALUES (?, ?, ?, ?, ?, ?, ?)", sample_alternatives)

        # Sample student
        cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
        student_count = cursor.fetchone()[0]
        
        if student_count == 0:
            student_password = bcrypt.hashpw("student123".encode('utf-8'), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (username, password, role, full_name, class_name)
                VALUES (?, ?, ?, ?, ?)
            ''', ("student1", student_password, "student", "Siswa Contoh", "XII IPA 1"))