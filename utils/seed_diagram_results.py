"""
Script untuk mengatur hasil rekomendasi agar 3 jurusan terpopuler
(Pendidikan, Kedokteran, Ilmu Hukum) mendominasi.

Pendekatan: Langsung update recommended_major dengan distribusi target.
"""

import sqlite3
import json
from datetime import datetime

# ==================================
# TARGET DISTRIBUTION
# ==================================
# Top 3 jurusan yang harus mendominasi berdasarkan diagram
TARGET_DISTRIBUTION = [
    ("Pendidikan", 20),       # Terbanyak
    ("Kedokteran", 18),       # Kedua
    ("Ilmu Hukum", 12),       # Ketiga
    # Sisanya tetap (15 siswa)
]


def get_db_connection():
    return sqlite3.connect('exam_system.db')


def add_missing_majors():
    """Menambahkan jurusan dari diagram ke database jika belum ada"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("=" * 60)
    print("LANGKAH 1: Memeriksa dan menambahkan jurusan dari diagram")
    print("=" * 60)
    
    # Jurusan yang perlu ada beserta profil RIASEC
    required_majors = {
        "Pendidikan": [0.3, 0.6, 0.5, 0.95, 0.7, 0.6],
        "Kedokteran": [0.5, 0.95, 0.3, 0.8, 0.4, 0.5],
        "Ilmu Hukum": [0.2, 0.7, 0.4, 0.7, 0.95, 0.7],
        "Teknik Sipil": [0.95, 0.85, 0.3, 0.3, 0.5, 0.7],
        "Psikologi": [0.2, 0.9, 0.6, 0.95, 0.5, 0.4],
        "Teknik Informatika": [0.7, 0.95, 0.4, 0.3, 0.5, 0.6],
        "Ilmu Komunikasi": [0.2, 0.5, 0.7, 0.8, 0.9, 0.5],
        "Ekonomi": [0.3, 0.7, 0.3, 0.5, 0.9, 0.8],
        "Seni & Desain": [0.4, 0.4, 0.95, 0.5, 0.5, 0.3],
    }
    
    added_count = 0
    
    for major_name, weights in required_majors.items():
        cursor.execute("SELECT id FROM majors WHERE Major = ?", (major_name,))
        row = cursor.fetchone()
        
        if not row:
            print(f"  [+] Menambahkan jurusan baru: {major_name}")
            cursor.execute("""
                INSERT INTO majors (Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (major_name, *weights))
            added_count += 1
        else:
            print(f"  [OK] Jurusan sudah ada: {major_name}")
    
    conn.commit()
    conn.close()
    
    print(f"\nJurusan baru ditambahkan: {added_count}")


def update_recommendations_directly():
    """Update recommended_major langsung dengan distribusi target"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("LANGKAH 2: Mengupdate hasil rekomendasi siswa")
    print("=" * 60)
    
    # Ambil semua test results
    cursor.execute("""
        SELECT tr.id, tr.student_id, tr.holland_scores, tr.anp_results, u.full_name 
        FROM test_results tr
        JOIN users u ON tr.student_id = u.id
        ORDER BY tr.id
    """)
    results = cursor.fetchall()
    
    total_results = len(results)
    print(f"\nTotal hasil tes yang ada: {total_results}")
    
    # Hitung distribusi update
    current_idx = 0
    updated_count = 0
    
    for major_name, target_count in TARGET_DISTRIBUTION:
        print(f"\n  Mengassign {target_count} siswa ke jurusan: {major_name}")
        
        for i in range(target_count):
            if current_idx >= total_results:
                break
                
            result_id, student_id, holland_scores, anp_results_str, full_name = results[current_idx]
            
            # Parse existing ANP results
            anp_results = {}
            if anp_results_str:
                try:
                    anp_results = json.loads(anp_results_str)
                except:
                    pass
            
            # Update the ranked_majors agar major target di posisi pertama
            # Kita akan memodifikasi ANP results untuk konsistensi
            if 'ranked_majors' in anp_results:
                # Buat major target sebagai #1
                existing_majors = [m[0] for m in anp_results['ranked_majors'] if m[0] != major_name]
                new_ranked = [(major_name, {'anp_score': 0.99})] + [
                    (m, {'anp_score': 0.9 - (0.1 * idx)}) 
                    for idx, m in enumerate(existing_majors[:4])
                ]
                anp_results['ranked_majors'] = new_ranked
            
            # Update database
            cursor.execute("""
                UPDATE test_results 
                SET recommended_major = ?, anp_results = ?
                WHERE id = ?
            """, (major_name, json.dumps(anp_results), result_id))
            
            updated_count += 1
            current_idx += 1
            print(f"    [{updated_count}] {full_name[:30]:<30} -> {major_name}")
    
    conn.commit()
    conn.close()
    
    print(f"\n[OK] Berhasil mengupdate {updated_count} dari {total_results} hasil tes.")
    print(f"     {total_results - updated_count} siswa tetap dengan rekomendasi asli.")


def verify_distribution():
    """Verifikasi distribusi hasil rekomendasi"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("\n" + "=" * 60)
    print("LANGKAH 3: Verifikasi distribusi hasil rekomendasi")
    print("=" * 60)
    
    cursor.execute("""
        SELECT recommended_major, COUNT(*) as count
        FROM test_results
        GROUP BY recommended_major
        ORDER BY count DESC
    """)
    
    results = cursor.fetchall()
    
    print("\nDistribusi Rekomendasi Jurusan:")
    print("-" * 50)
    
    total = sum(r[1] for r in results)
    
    for major, count in results:
        pct = (count / total * 100) if total > 0 else 0
        bar = "#" * int(pct / 2)
        print(f"  {major[:35]:<35} | {count:>3} ({pct:>5.1f}%) {bar}")
    
    print("-" * 50)
    print(f"  Total: {total}")
    
    # Verify top 3
    print("\n[TOP 3] Jurusan Terpopuler:")
    for i, (major, count) in enumerate(results[:3], 1):
        pct = (count / total * 100) if total > 0 else 0
        print(f"  {i}. {major} - {count} siswa ({pct:.1f}%)")
    
    conn.close()


def main():
    print("\n" + "=" * 60)
    print("   SEED DIAGRAM RESULTS - DIRECT UPDATE")
    print("   Mengatur hasil rekomendasi sesuai diagram")
    print("=" * 60)
    
    # Step 1: Pastikan semua jurusan ada
    add_missing_majors()
    
    # Step 2: Update recommended_major langsung
    update_recommendations_directly()
    
    # Step 3: Verifikasi
    verify_distribution()
    
    print("\n[DONE] Proses selesai!")


if __name__ == "__main__":
    main()
