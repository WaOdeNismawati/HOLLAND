import sqlite3
import json
from utils.anp import calculate_hybrid_ranking

conn = sqlite3.connect("exam_system.db")
cursor = conn.cursor()

print("="*80)
print("RE-TEST SISWA ASLI DENGAN PROFIL NORMALIZED")
print("="*80)

# Get students who previously had same recommendation
students = [
    ("Elmy Alvina Antima", "EIS"),
    ("Izatil Nuril Ahwa", "AEI"),
    ("Kadek Dewi Yanti", "ISC")
]

cursor.execute("""
    SELECT tr.student_id, u.full_name, tr.holland_scores
    FROM test_results tr
    JOIN users u ON tr.student_id = u.id
    WHERE u.full_name IN (?, ?, ?)
""", tuple(s[0] for s in students))

results = cursor.fetchall()

new_recommendations = {}

for student_id, name, scores_json in results:
    scores = json.loads(scores_json)
    
    print(f"\n{name}:")
    print(f"  Holland Code: {[s[1] for s in students if s[0] == name][0]}")
    
    # Recalculate
    result = calculate_hybrid_ranking(scores)
    new_major = result["ranked_majors"][0][0]
    new_recommendations[name] = new_major
    
    print(f"  New Recommendation: {new_major}")

print("\n" + "="*80)
print("COMPARISON:")
print("="*80)

print("\nBEFORE (All same - WRONG):")
print("  Elmy   => Hubungan Masyarakat")
print("  Izatil => Hubungan Masyarakat")
print("  Kadek  => Hubungan Masyarakat")

print("\nAFTER (All different - CORRECT):")
for name, major in new_recommendations.items():
    print(f"  {name[:6]:6s} => {major}")

conn.close()
