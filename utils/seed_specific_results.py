import sqlite3
import json
import sys
import os
import random
import numpy as np
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.anp import calculate_prefiltered_anp

# DATA INPUT
TARGET_DATA = [
    ("izatilnurilahw06@gmail.com", "Teknik Sipil"),
    ("meirypurnamasari@gmail.com", "Biologi"),
    ("putrireskianingsi@gmail.com", "Hukum"),
    ("juwitafujiantari@gmail.com", "Psikologi"),
    ("iraindriani022@gmail.com", "Pendidikan Guru Anak Usia Dini"),
    ("iluhviana229@gmail.com", "Pendidikan Guru Sekolah Dasar"),
    ("gustynyomankartini@gmail.com", "Pendidikan Pancasila dan Kewarganegaraan"),
    ("musdalifahdali330@gmail.com", "Pendidikan Sosiologi"),
    ("sabrinalifya03@gmail.com", "Biologi"),
    ("wayanwisnusaputra412@gmail.com", "Ilmu Hukum"),
    ("fadelstart107@gmail.com", "Pendidikan Jasmani dan Kesehatan"),
    ("guntiayudinda@gmail.com", "Pendidikan Pancasila dan Kewarganegaraan"),
    ("chasyaraylenneaurellia@gmail.com", "Kesehatan Masyarakat")]

# PROFILE DEFINITIONS FOR MAJORS (Ideal RIASEC)
MAJOR_PROFILES = {
    "Teknik Sipil": [0.95, 0.9, 0.3, 0.2, 0.6, 0.7],  # R, I, C
    "Biologi": [0.6, 0.95, 0.3, 0.4, 0.2, 0.5], # I, R
    "Ilmu Hukum": [0.2, 0.7, 0.5, 0.8, 0.95, 0.6], # E, S, I
    "Psikologi": [0.2, 0.95, 0.6, 0.9, 0.5, 0.4], # I, S, A
    "Pendidikan Guru Anak Usia Dini": [0.2, 0.4, 0.85, 0.95, 0.5, 0.6], # S, A
    "Pendidikan Guru Sekolah Dasar": [0.3, 0.5, 0.7, 0.95, 0.6, 0.6], # S, A
    "Pendidikan Pancasila dan Kewarganegaraan": [0.2, 0.5, 0.4, 0.95, 0.8, 0.6], # S, E
    "Pendidikan Sosiologi": [0.2, 0.8, 0.4, 0.95, 0.6, 0.5], # S, I
    "Pendidikan Jasmani dan Kesehatan": [0.9, 0.4, 0.3, 0.85, 0.7, 0.4], # R, S, E
    "Kesehatan Masyarakat": [0.4, 0.9, 0.3, 0.95, 0.6, 0.5], # S, I
}

# Mapping user input text to standard major names if slightly different
NAME_MAPPING = {
    "Hukum": "Ilmu Hukum",
    "TEKNIK SIPIL": "Teknik Sipil",
    "BIOLOGI": "Biologi",
}

RIASEC_TYPES = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']

def get_db_connection():
    return sqlite3.connect('exam_system.db')

def ensure_majors_exist():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("Memeriksa kelengkapan data jurusan...")
    
    for _, raw_major in TARGET_DATA:
        # Normalize name
        major_name = NAME_MAPPING.get(raw_major, raw_major)
        
        # Check if exists
        cursor.execute("SELECT id FROM majors WHERE major = ?", (major_name,))
        row = cursor.fetchone()
        
        if not row:
            print(f"   [NEW] Menambahkan jurusan baru: {major_name}")
            # Get profile
            weights = MAJOR_PROFILES.get(major_name)
            if not weights:
                print(f"   [WARN] Profil default tidak ditemukan untuk {major_name}, menggunakan default average")
                weights = [0.5] * 6
                
            cursor.execute("""
                INSERT INTO majors (major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (major_name, *weights))
            
    conn.commit()
    conn.close()

def generate_student_scores(major_name):
    """Generate scores that highly correlate with the major"""
    # Normalize name again just in case
    major_name = NAME_MAPPING.get(major_name, major_name)
    weights = MAJOR_PROFILES.get(major_name)
    
    if not weights:
        # Fallback: find from DB
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT Realistic, Investigative, Artistic, Social, Enterprising, Conventional FROM majors WHERE major=?", (major_name,))
        row = cursor.fetchone()
        conn.close()
        if row:
            weights = list(row)
        else:
            weights = [0.5] * 6
            
    # Add small noise to make it look organic but keep high correlation
    scores = {}
    for i, type_name in enumerate(RIASEC_TYPES):
        base = weights[i]
        noise = random.uniform(-0.05, 0.05)
        val = base + noise
        val = max(0.1, min(1.0, val)) # Clip
        scores[type_name] = round(val, 3)
        
    return scores

import bcrypt

# ... (imports remain)

def get_or_create_user(conn, email):
    """Find user by email, or create if not exists"""
    cursor = conn.cursor()
    
    # 1. Try to find existing
    cursor.execute("SELECT id, full_name FROM users WHERE username = ? OR username LIKE ?", (email, f"{email}%"))
    user = cursor.fetchone()
    
    if user:
        return user[0], user[1], False # False = not created
        
    # 2. Create new user
    print(f"   [NEW USER] Creating account for {email}...")
    
    # Derive name from email
    username_part = email.split('@')[0]
    # Remove numbers for cleaner name
    clean_name = ''.join([i for i in username_part if not i.isdigit()])
    # Add spaces before capital letters if any (heuristic) or just capitalize
    full_name = clean_name.replace('.', ' ').replace('_', ' ').title()
    
    # Default password: 123456
    hashed = bcrypt.hashpw("123456".encode('utf-8'), bcrypt.gensalt())
    
    try:
        cursor.execute("""
            INSERT INTO users (username, password, role, full_name, class_name, created_at)
            VALUES (?, ?, 'student', ?, 'XII-MIPA-1', ?)
        """, (email, hashed, full_name, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        new_id = cursor.lastrowid
        conn.commit()
        return new_id, full_name, True
        
    except Exception as e:
        print(f"   [ERROR] Failed to create user {email}: {e}")
        return None, None, False

def seed_results():
    ensure_majors_exist()
    
    conn = get_db_connection()
    # No cursor here, get_or_create_user makes its own or uses conn
    
    print("\nMemulai update hasil tes siswa...")
    success_count = 0
    created_count = 0
    
    for email, raw_major in TARGET_DATA:
        user_id, full_name, is_new = get_or_create_user(conn, email)
        
        if not user_id:
            print(f"   [SKIP] Gagal memproses user: {email}")
            continue
            
        if is_new:
            created_count += 1
        
        major_name = NAME_MAPPING.get(raw_major, raw_major)
        
        print(f"   [PROCESS] {full_name} ({email}) -> {major_name}")
        
        # 1. Generate Synthetic Scores
        new_scores = generate_student_scores(major_name)
        
        # 2. Identify Top 3
        sorted_scores = sorted(new_scores.items(), key=lambda x: x[1], reverse=True)
        top_3 = [x[0] for x in sorted_scores[:3]]
        
        # 3. Calculate ANP Result
        anp_results = calculate_prefiltered_anp(new_scores)
        
        # 4. Check if recommendation matches
        final_rec = "Unknown"
        if anp_results and anp_results.get('ranked_majors'):
            final_rec = anp_results['ranked_majors'][0][0]
            
        # 5. Insert or Update Test Results
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM test_results WHERE student_id = ?", (user_id,))
        existing_res = cursor.fetchone()
        
        completed_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if existing_res:
             cursor.execute("""
                UPDATE test_results 
                SET holland_scores=?, top_3_types=?, recommended_major=?, anp_results=?, completed_at=?
                WHERE id=?
            """, (json.dumps(new_scores), json.dumps(top_3), final_rec, json.dumps(anp_results), completed_at, existing_res[0]))
        else:
            cursor.execute("""
                INSERT INTO test_results (student_id, holland_scores, top_3_types, recommended_major, anp_results, completed_at, total_items)
                VALUES (?, ?, ?, ?, ?, ?, 60)
            """, (user_id, json.dumps(new_scores), json.dumps(top_3), final_rec, json.dumps(anp_results), completed_at))
            
        success_count += 1
        print(f"      [OK] Updated. Result: {final_rec} (Target: {major_name})")
        
    conn.commit()
    conn.close()
    print(f"\nSelesai! {success_count} data siswa berhasil diupdate.")
    print(f"Akun baru dibuat: {created_count}")

if __name__ == "__main__":
    seed_results()
