import sqlite3
import json
import sys
import os

# Add parent directory to path to allow imports from utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.anp import calculate_prefiltered_anp

def recalculate_all():
    db_path = 'exam_system.db'
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("Membaca data hasil tes lama...")
        cursor.execute("SELECT id, student_id, holland_scores FROM test_results")
        rows = cursor.fetchall()
        
        print(f"Ditemukan {len(rows)} data hasil tes. Memulai perhitungan ulang...")
        
        updated_count = 0
        
        for row in rows:
            result_id = row[0]
            student_id = row[1]
            scores_json = row[2]
            
            if not scores_json:
                continue
                
            try:
                # 1. Parse Holland Scores
                holland_scores = json.loads(scores_json)
                
                # 2. Re-run ANP Calculation (using NEW major weights)
                # calculate_prefiltered_anp loads majors from DB internally
                anp_results = calculate_prefiltered_anp(holland_scores)
                
                # 3. Determine new recommendation
                new_recommended_major = "Tidak ada rekomendasi"
                if anp_results and anp_results.get('ranked_majors'):
                    new_recommended_major = anp_results['ranked_majors'][0][0]
                
                # 4. Update Database
                cursor.execute("""
                    UPDATE test_results 
                    SET anp_results = ?, recommended_major = ?
                    WHERE id = ?
                """, (json.dumps(anp_results), new_recommended_major, result_id))
                
                updated_count += 1
                if updated_count % 5 == 0:
                    print(f"   Processed {updated_count}...")
                    
            except Exception as e:
                print(f"   [Error] ID {result_id}: {e}")
        
        conn.commit()
        conn.close()
        print(f"\n✅ Berhasil memperbarui {updated_count} data hasil tes dengan bobot jurusan baru.")
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")

if __name__ == "__main__":
    recalculate_all()
