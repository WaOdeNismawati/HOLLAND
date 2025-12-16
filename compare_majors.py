import sqlite3
import json
import numpy as np

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print("="*60)
print("ANALISIS: Keperawatan vs Pendidikan")
print("="*60)

# Check profil
cursor.execute('''
    SELECT Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional
    FROM majors
    WHERE Major IN ('Keperawatan', 'Pendidikan')
    ORDER BY Major
''')
majors = cursor.fetchall()

print(f"\nProfil RIASEC:\n")
for major_data in majors:
    major = major_data[0]
    r, i, a, s, e, c = major_data[1:]
    print(f"{major:20s} R:{r:.3f} I:{i:.3f} A:{a:.3f} S:{s:.3f} E:{e:.3f} C:{c:.3f}")
    total = r + i + a + s + e + c
    print(f"{'':20s} Total: {total:.3f}\n")

# Check student score
cursor.execute('SELECT holland_scores FROM test_results WHERE student_id = 8')
result = cursor.fetchone()
if result:
    scores = json.loads(result[0])
    print("Student ID 8 (normalized scores):")
    print(f"  R:{scores['Realistic']:.3f} I:{scores['Investigative']:.3f} A:{scores['Artistic']:.3f}")
    print(f"  S:{scores['Social']:.3f} E:{scores['Enterprising']:.3f} C:{scores['Conventional']:.3f}\n")
    
    # Simulate weighted scoring for both majors
    print("Simulasi Weighted Score (tanpa criteria weights):")
    for major_data in majors:
        major = major_data[0]
        r, i, a, s, e, c = major_data[1:]
        
        # Simple dot product
        score = (r * scores['Realistic'] + 
                 i * scores['Investigative'] +
                 a * scores['Artistic'] +
                 s * scores['Social'] +
                 e * scores['Enterprising'] +
                 c * scores['Conventional'])
        
        # Cosine similarity
        student_vec = np.array([scores['Realistic'], scores['Investigative'], 
                                scores['Artistic'], scores['Social'],
                                scores['Enterprising'], scores['Conventional']])
        major_vec = np.array([r, i, a, s, e, c])
        similarity = np.dot(student_vec, major_vec) / (np.linalg.norm(student_vec) * np.linalg.norm(major_vec))
        
        print(f"\n{major}:")
        print(f"  Dot product: {score:.4f}")
        print(f"  Cosine sim:  {similarity:.4f}")

conn.close()
