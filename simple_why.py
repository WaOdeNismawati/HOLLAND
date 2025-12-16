import sqlite3
import json

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print("="*60)
print("WHY MUSIK WINS?")
print("="*60)

cursor.execute('SELECT holland_scores FROM test_results WHERE student_id = 8')
result = cursor.fetchone()
student_scores = json.loads(result[0])

competitors = ['Musik', 'Pendidikan']
cursor.execute('SELECT Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional FROM majors WHERE Major IN (?, ?)', competitors)
majors = cursor.fetchall()

print(f"\nStudent SAE:")
print(f"  S:{student_scores['Social']:.3f} A:{student_scores['Artistic']:.3f} E:{student_scores['Enterprising']:.3f}")
print(f"  R:{student_scores['Realistic']:.3f} I:{student_scores['Investigative']:.3f} C:{student_scores['Conventional']:.3f}\n")

for major_data in majors:
    major = major_data[0]
    r, i, a, s, e, c = major_data[1:]
    
    contrib_s = s * student_scores['Social']
    contrib_a = a * student_scores['Artistic']
    contrib_e = e * student_scores['Enterprising']
    contrib_i = i * student_scores['Investigative']
    contrib_r = r * student_scores['Realistic']
    contrib_c = c * student_scores['Conventional']
    
    total = contrib_s + contrib_a + contrib_e + contrib_i + contrib_r + contrib_c
    
    print(f"{major}:")
    print(f"  Profile: S:{s:.3f} A:{a:.3f} E:{e:.3f} I:{i:.3f} R:{r:.3f} C:{c:.3f}")
    print(f"  Top contributions:")
    print(f"    S: {s:.3f} x {student_scores['Social']:.3f} = {contrib_s:.4f}")
    print(f"    A: {a:.3f} x {student_scores['Artistic']:.3f} = {contrib_a:.4f}")
    print(f"    E: {e:.3f} x {student_scores['Enterprising']:.3f} = {contrib_e:.4f}")
    print(f"  Total: {total:.4f}\n")

print("="*60)
print("SOLUTION: Make A and E very LOW, S very HIGH")
print("="*60)

conn.close()
