"""
Script untuk recalculate semua test results dengan profil jurusan yang sudah dinormalisasi.
"""
import sqlite3
import json
from utils.anp import calculate_hybrid_ranking

conn = sqlite3.connect("exam_system.db")
cursor = conn.cursor()

print("="*80)
print("RECALCULATE ALL TEST RESULTS")
print("="*80)

cursor.execute("""
    SELECT tr.student_id, u.full_name, tr.holland_scores, tr.top_3_types
    FROM test_results tr
    JOIN users u ON tr.student_id = u.id
""")

results = cursor.fetchall()

print(f"\nTotal students: {len(results)}")

if len(results) == 0:
    print("No test results. Exiting.")
    exit()

print("\nRecalculating with normalized profiles...")

updated = 0

for student_id, name, scores_json, top_3_json in results:
    scores = json.loads(scores_json)
    
    try:
        anp_results = calculate_hybrid_ranking(scores)
        
        if anp_results and anp_results["ranked_majors"]:
            new_major = anp_results["ranked_majors"][0][0]
            
            cursor.execute("""
                UPDATE test_results
                SET recommended_major = ?,
                    anp_results = ?
                WHERE student_id = ?
            """, (
                new_major,
                json.dumps({"anp_results": anp_results}),
                student_id
            ))
            
            print(f"  {name:30s} => {new_major}")
            updated += 1
        else:
            print(f"  {name:30s} (No results)")
            
    except Exception as e:
        print(f"  {name:30s} ERROR: {e}")

conn.commit()
conn.close()

print(f"\n[DONE] Updated {updated}/{len(results)} students")
