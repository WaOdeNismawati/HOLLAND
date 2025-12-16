import sqlite3
import json
import numpy as np

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print("="*60)
print("WHY MUSIK WINS? DEEP ANALYSIS")
print("="*60)

# Get student score
cursor.execute('SELECT holland_scores FROM test_results WHERE student_id = 8')
result = cursor.fetchone()
student_scores = json.loads(result[0])

# Get top competitors
competitors = ['Musik', 'Pendidikan', 'Keperawatan', 'Kesehatan Masyarakat']
cursor.execute(f'''
    SELECT Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional
    FROM majors
    WHERE Major IN ({','.join(['?']*len(competitors))})
''', competitors)
majors = cursor.fetchall()

print(f"\nStudent Score (SAE):")
for key in ['Social', 'Artistic', 'Enterprising', 'Realistic', 'Investigative', 'Conventional']:
    print(f"  {key[0]}: {student_scores[key]:.3f}")

print(f"\n{'='*60}")
print("COMPARISON (simple weighted score simulation):\n")

for major_data in majors:
    major = major_data[0]
    r, i, a, s, e, c = major_data[1:]
    
    # Calculate contributions
    contrib = {
        'R': r * student_scores['Realistic'],
        'I': i * student_scores['Investigative'],
        'A': a * student_scores['Artistic'],
        'S': s * student_scores['Social'],
        'E': e * student_scores['Enterprising'],
        'C': c * student_scores['Conventional']
    }
    total = sum(contrib.values())
    
    print(f"{major}:")
    print(f"  Major profile: R:{r:.3f} I:{i:.3f} A:{a:.3f} S:{s:.3f} E:{e:.3f} C:{c:.3f}")
    print(f"  Contributions:")
    for riasec, val in sorted(contrib.items(), key=lambda x: -x[1]):
        print(f"    {riasec}: {val:.4f} (major:{major_data[1+['R','I','A','S','E','C'].index(riasec)]:.3f} × student:{student_scores[['Realistic','Investigative','Artistic','Social','Enterprising','Conventional'][['R','I','A','S','E','C'].index(riasec)]]:.3f})")
    print(f"  Total: {total:.4f}\n")

print("="*60)
print("INSIGHT: Musik menang karena A:0.937 × student_A:0.800 = 0.75")
print("         Untuk beat Musik, kita perlu S contribution >> A contribution")
print("         Social harus SANGAT tinggi, Artistic harus RENDAH")
print("="*60)

conn.close()
