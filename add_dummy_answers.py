"""
Script untuk menambahkan jawaban dummy siswa dengan pola SANGAT BERVARIASI.
Menggunakan 30+ profil berbeda + variasi acak untuk memaksimalkan keragaman rekomendasi.
"""
import sqlite3
import sys
import os
import random

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.holland_calculator import HollandCalculator

def add_dummy_answers_and_process():
    conn = sqlite3.connect('exam_system.db')
    cur = conn.cursor()
    
    # Ambil semua siswa
    cur.execute("SELECT id, username FROM users WHERE role='student'")
    students = cur.fetchall()
    print(f"Ditemukan {len(students)} siswa")
    
    # Ambil semua pertanyaan berdasarkan tipe Holland
    cur.execute("SELECT id, holland_type FROM questions ORDER BY id")
    questions = cur.fetchall()
    print(f"Ditemukan {len(questions)} pertanyaan\n")
    
    # Kelompokkan pertanyaan berdasarkan tipe Holland
    questions_by_type = {}
    for q_id, h_type in questions:
        if h_type not in questions_by_type:
            questions_by_type[h_type] = []
        questions_by_type[h_type].append(q_id)
    
    # 30+ PROFIL YANG SANGAT BERBEDA
    # Setiap profil mewakili kombinasi Holland yang unik
    dummy_profiles = [
        # === TIPE TUNGGAL DOMINAN ===
        # 1. Pure Realistic
        {'Realistic': 5, 'Investigative': 2, 'Artistic': 1, 'Social': 1, 'Enterprising': 1, 'Conventional': 2},
        # 2. Pure Investigative
        {'Realistic': 2, 'Investigative': 5, 'Artistic': 1, 'Social': 1, 'Enterprising': 1, 'Conventional': 2},
        # 3. Pure Artistic
        {'Realistic': 1, 'Investigative': 1, 'Artistic': 5, 'Social': 2, 'Enterprising': 1, 'Conventional': 1},
        # 4. Pure Social
        {'Realistic': 1, 'Investigative': 1, 'Artistic': 2, 'Social': 5, 'Enterprising': 2, 'Conventional': 1},
        # 5. Pure Enterprising
        {'Realistic': 1, 'Investigative': 1, 'Artistic': 1, 'Social': 2, 'Enterprising': 5, 'Conventional': 2},
        # 6. Pure Conventional
        {'Realistic': 2, 'Investigative': 1, 'Artistic': 1, 'Social': 1, 'Enterprising': 2, 'Conventional': 5},
        
        # === KOMBINASI DUA TIPE (Adjacent di Hexagon) ===
        # 7. RI - Realistic + Investigative (Engineer/Scientist)
        {'Realistic': 5, 'Investigative': 5, 'Artistic': 1, 'Social': 1, 'Enterprising': 1, 'Conventional': 2},
        # 8. IA - Investigative + Artistic (Architect/Designer)
        {'Realistic': 1, 'Investigative': 5, 'Artistic': 5, 'Social': 2, 'Enterprising': 1, 'Conventional': 1},
        # 9. AS - Artistic + Social (Art Teacher/Counselor)
        {'Realistic': 1, 'Investigative': 1, 'Artistic': 5, 'Social': 5, 'Enterprising': 2, 'Conventional': 1},
        # 10. SE - Social + Enterprising (HR/Sales Manager)
        {'Realistic': 1, 'Investigative': 1, 'Artistic': 2, 'Social': 5, 'Enterprising': 5, 'Conventional': 2},
        # 11. EC - Enterprising + Conventional (Business/Finance)
        {'Realistic': 1, 'Investigative': 2, 'Artistic': 1, 'Social': 2, 'Enterprising': 5, 'Conventional': 5},
        # 12. CR - Conventional + Realistic (Industrial Engineer)
        {'Realistic': 5, 'Investigative': 2, 'Artistic': 1, 'Social': 1, 'Enterprising': 2, 'Conventional': 5},
        
        # === KOMBINASI DUA TIPE (Opposite di Hexagon) - Kurang Umum ===
        # 13. RA - Realistic + Artistic (Craftsman/Industrial Designer)
        {'Realistic': 5, 'Investigative': 2, 'Artistic': 5, 'Social': 1, 'Enterprising': 1, 'Conventional': 1},
        # 14. IS - Investigative + Social (Medical Doctor/Psychologist)
        {'Realistic': 2, 'Investigative': 5, 'Artistic': 1, 'Social': 5, 'Enterprising': 1, 'Conventional': 2},
        # 15. AE - Artistic + Enterprising (Creative Director/Producer)
        {'Realistic': 1, 'Investigative': 1, 'Artistic': 5, 'Social': 2, 'Enterprising': 5, 'Conventional': 1},
        # 16. SC - Social + Conventional (Administrator/HR)
        {'Realistic': 1, 'Investigative': 2, 'Artistic': 1, 'Social': 5, 'Enterprising': 2, 'Conventional': 5},
        # 17. RE - Realistic + Enterprising (Contractor/Business Owner)
        {'Realistic': 5, 'Investigative': 1, 'Artistic': 1, 'Social': 2, 'Enterprising': 5, 'Conventional': 2},
        # 18. IC - Investigative + Conventional (Accountant/Analyst)
        {'Realistic': 2, 'Investigative': 5, 'Artistic': 1, 'Social': 1, 'Enterprising': 2, 'Conventional': 5},
        
        # === KOMBINASI TIGA TIPE ===
        # 19. RIA - Realistic + Investigative + Artistic
        {'Realistic': 5, 'Investigative': 5, 'Artistic': 4, 'Social': 1, 'Enterprising': 1, 'Conventional': 1},
        # 20. IAS - Investigative + Artistic + Social
        {'Realistic': 1, 'Investigative': 5, 'Artistic': 5, 'Social': 4, 'Enterprising': 1, 'Conventional': 1},
        # 21. ASE - Artistic + Social + Enterprising
        {'Realistic': 1, 'Investigative': 1, 'Artistic': 5, 'Social': 5, 'Enterprising': 4, 'Conventional': 1},
        # 22. SEC - Social + Enterprising + Conventional
        {'Realistic': 1, 'Investigative': 1, 'Artistic': 1, 'Social': 5, 'Enterprising': 5, 'Conventional': 4},
        # 23. ECR - Enterprising + Conventional + Realistic
        {'Realistic': 4, 'Investigative': 1, 'Artistic': 1, 'Social': 1, 'Enterprising': 5, 'Conventional': 5},
        # 24. CRI - Conventional + Realistic + Investigative
        {'Realistic': 5, 'Investigative': 4, 'Artistic': 1, 'Social': 1, 'Enterprising': 1, 'Conventional': 5},
        
        # === PROFIL KHUSUS UNTUK JURUSAN SPESIFIK ===
        # 25. Teknik (R dominan, I C pendukung)
        {'Realistic': 5, 'Investigative': 4, 'Artistic': 1, 'Social': 1, 'Enterprising': 2, 'Conventional': 4},
        # 26. Kedokteran (I S dominan)
        {'Realistic': 3, 'Investigative': 5, 'Artistic': 1, 'Social': 5, 'Enterprising': 1, 'Conventional': 2},
        # 27. Desain (A dominan, I pendukung)
        {'Realistic': 2, 'Investigative': 3, 'Artistic': 5, 'Social': 2, 'Enterprising': 2, 'Conventional': 1},
        # 28. Manajemen (E S dominan)
        {'Realistic': 1, 'Investigative': 2, 'Artistic': 1, 'Social': 4, 'Enterprising': 5, 'Conventional': 3},
        # 29. Hukum (E S C)
        {'Realistic': 1, 'Investigative': 3, 'Artistic': 1, 'Social': 4, 'Enterprising': 5, 'Conventional': 4},
        # 30. IT/Komputer (R I dominan)
        {'Realistic': 4, 'Investigative': 5, 'Artistic': 2, 'Social': 1, 'Enterprising': 2, 'Conventional': 3},
        
        # === PROFIL TAMBAHAN UNTUK VARIASI ===
        # 31. Seimbang Tinggi
        {'Realistic': 4, 'Investigative': 4, 'Artistic': 4, 'Social': 4, 'Enterprising': 4, 'Conventional': 4},
        # 32. Seimbang Menengah
        {'Realistic': 3, 'Investigative': 3, 'Artistic': 3, 'Social': 3, 'Enterprising': 3, 'Conventional': 3},
        # 33. RIC (Technical Analyst)
        {'Realistic': 5, 'Investigative': 4, 'Artistic': 1, 'Social': 1, 'Enterprising': 1, 'Conventional': 5},
        # 34. SAE (Creative Educator)
        {'Realistic': 1, 'Investigative': 2, 'Artistic': 4, 'Social': 5, 'Enterprising': 4, 'Conventional': 1},
        # 35. RCE (Operations Manager)
        {'Realistic': 5, 'Investigative': 1, 'Artistic': 1, 'Social': 2, 'Enterprising': 4, 'Conventional': 5},
    ]
    
    # Inisialisasi Holland Calculator
    calculator = HollandCalculator()
    
    print("="*60)
    print("MEMASUKKAN JAWABAN DAN MEMPROSES HASIL TES")
    print(f"Menggunakan {len(dummy_profiles)} profil berbeda + variasi acak")
    print("="*60)
    
    processed_count = 0
    recommendation_tracker = {}
    
    # Shuffle students untuk variasi lebih
    random.seed(42)  # Untuk reproducibility
    shuffled_indices = list(range(len(students)))
    random.shuffle(shuffled_indices)
    
    for order, idx in enumerate(shuffled_indices):
        student_id, username = students[idx]
        
        # Pilih profil dan tambahkan variasi acak
        profile_idx = order % len(dummy_profiles)
        base_profile = dummy_profiles[profile_idx].copy()
        
        # Tambahkan variasi acak ±1 untuk beberapa nilai (tapi tetap dalam range 1-5)
        profile = {}
        for h_type, base_val in base_profile.items():
            variation = random.choice([-1, 0, 0, 0, 1])  # Lebih sering tidak berubah
            new_val = max(1, min(5, base_val + variation))
            profile[h_type] = new_val
        
        print(f"\n[{order+1}/{len(students)}] {username}")
        print(f"  R={profile['Realistic']}, I={profile['Investigative']}, "
              f"A={profile['Artistic']}, S={profile['Social']}, "
              f"E={profile['Enterprising']}, C={profile['Conventional']}")
        
        # 1. Hapus jawaban lama
        cur.execute("DELETE FROM student_answers WHERE student_id = ?", (student_id,))
        
        # 2. Input jawaban berdasarkan tipe Holland
        for h_type, q_ids in questions_by_type.items():
            answer_value = profile[h_type]
            for q_id in q_ids:
                cur.execute("""
                    INSERT INTO student_answers (student_id, question_id, answer)
                    VALUES (?, ?, ?)
                """, (student_id, q_id, answer_value))
        
        conn.commit()
        
        # 3. Proses hasil tes
        try:
            result = calculator.process_test_completion(student_id, total_items=len(questions))
            processed_count += 1
            recommended = result['recommended_major']
            
            if recommended not in recommendation_tracker:
                recommendation_tracker[recommended] = 0
            recommendation_tracker[recommended] += 1
            
            print(f"  → {result['holland_code']} → {recommended}")
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    print("\n" + "="*60)
    print("RINGKASAN DISTRIBUSI REKOMENDASI")
    print("="*60)
    
    total_recommendations = sum(recommendation_tracker.values())
    print(f"\nTotal: {total_recommendations} siswa, {len(recommendation_tracker)} jurusan berbeda\n")
    
    for major, count in sorted(recommendation_tracker.items(), key=lambda x: -x[1]):
        pct = (count / total_recommendations) * 100 if total_recommendations > 0 else 0
        bar = "█" * int(pct / 2)
        print(f"  {major:30s} {count:3d} ({pct:5.1f}%) {bar}")
    
    conn.close()
    print(f"\n✅ Berhasil memproses {processed_count} siswa!")

if __name__ == "__main__":
    add_dummy_answers_and_process()
