import sqlite3
import json
import pandas as pd
import numpy as np

def get_detailed_calculation():
    conn = sqlite3.connect('exam_system.db')
    cursor = conn.cursor()
    
    # Ambil 1 siswa
    cursor.execute('''
        SELECT u.full_name, tr.holland_scores, tr.anp_results 
        FROM test_results tr 
        JOIN users u ON tr.student_id = u.id 
        LIMIT 1
    ''')
    row = cursor.fetchone()
    if not row:
        print("No student data found.")
        return

    name = row[0]
    scores = json.loads(row[1]) if isinstance(row[1], str) else row[1]
    anp = json.loads(row[2]) if isinstance(row[2], str) else row[2]
    
    print(f"=== PERHITUNGAN LENGKAP ANP: {name} ===")
    print("\n1. SKOR RIASEC (CRITERIA SCORES)")
    for k, v in scores.items():
        print(f"   - {k}: {v}")
    
    details = anp.get('calculation_details', {})
    
    print("\n2. BOBOT PRIORITAS KRITERIA (CRITERIA WEIGHTS)")
    cp = details.get('criteria_priorities', {})
    for k, v in cp.items():
        print(f"   - {k}: {v:.4f}")
    
    print(f"\n3. CONSISTENCY RATIO (CR): {details.get('consistency_ratio', 0):.4f}")
    print(f"   Status: {'Konsisten' if details.get('is_consistent') else 'Tidak Konsisten'}")
    
    print("\n4. TOP 5 REKOMENDASI JURUSAN (FINAL PRIORITY)")
    ranked = anp.get('top_5_majors', [])
    for i, item in enumerate(ranked, 1):
        major = item.get('major_name')
        score = item.get('anp_score')
        print(f"   {i}. {major}: {score:.4f}")

    conn.close()

if __name__ == "__main__":
    get_detailed_calculation()
