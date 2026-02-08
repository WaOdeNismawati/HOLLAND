
import os
import sys
import json
import sqlite3
from datetime import datetime

# Menambahkan directory root ke sys.path agar bisa import module lokal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.db_manager import DatabaseManager
from utils.holland_calculator import HollandCalculator

def recalculate_all_results():
    print("=== Memulai Kalkulasi Ulang Jawaban Siswa ===")
    
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # 1. Ambil semua student_id yang sudah memberikan jawaban
    cursor.execute("SELECT DISTINCT student_id FROM student_answers")
    student_ids = [row[0] for row in cursor.fetchall()]
    
    if not student_ids:
        print("Tidak ada data jawaban siswa untuk dihitung ulang.")
        conn.close()
        return

    print(f"Ditemukan {len(student_ids)} siswa dengan jawaban.")
    
    calculator = HollandCalculator()
    
    success_count = 0
    fail_count = 0
    
    for student_id in student_ids:
        # Ambil nama siswa untuk log
        cursor.execute("SELECT full_name FROM users WHERE id = ?", (student_id,))
        user_row = cursor.fetchone()
        student_name = user_row[0] if user_row else f"Unknown (ID: {student_id})"
        
        # Ambil total_items lama jika ada
        cursor.execute("SELECT total_items FROM test_results WHERE student_id = ?", (student_id,))
        result_row = cursor.fetchone()
        total_items = result_row[0] if result_row else 60 # Default ke 60 jika tidak ada
        
        print(f"Memproses [{student_id}] {student_name}...")
        
        try:
            # Jalankan kalkulasi ulang
            # process_test_completion akan menghitung skor, menjalankan ANP, dan menyimpan ke DB
            results = calculator.process_test_completion(student_id, total_items=total_items)
            print(f"  > Sukses: Rekomendasi -> {results['recommended_major']}")
            success_count += 1
        except Exception as e:
            print(f"  > GAGAL memproses {student_name}: {str(e)}")
            fail_count += 1
            
    conn.close()
    
    print("\n=== Kalkulasi Ulang Selesai ===")
    print(f"Total diproses: {len(student_ids)}")
    print(f"Berhasil     : {success_count}")
    print(f"Gagal        : {fail_count}")

if __name__ == "__main__":
    recalculate_all_results()
