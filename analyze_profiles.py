import sqlite3
import json

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print("="*60)
print("ANALISIS: Kenapa bukan Pendidikan?")
print("="*60)

# Check profil Musik, Psikologi, dan Pendidikan
cursor.execute('''
    SELECT Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional
    FROM majors
    WHERE Major IN ('Musik', 'Psikologi', 'Pendidikan')
    ORDER BY Major
''')
majors = cursor.fetchall()

print(f"\nProfil RIASEC Jurusan:\n")
for major_data in majors:
    major = major_data[0]
    r, i, a, s, e, c = major_data[1:]
    print(f"{major:20s} R:{r:.2f} I:{i:.2f} A:{a:.2f} S:{s:.2f} E:{e:.2f} C:{c:.2f}")
    riasec_dict = {'R': r, 'I': i, 'A': a, 'S': s, 'E': e, 'C': c}
    sorted_riasec = sorted(riasec_dict.items(), key=lambda x: x[1], reverse=True)
    top_3 = ''.join([code for code, _ in sorted_riasec[:3]])
    print(f"{'':20s} Top 3: {top_3}\n")

# Check skor siswa ID 8
cursor.execute('SELECT holland_scores FROM test_results WHERE student_id = 8')
result = cursor.fetchone()
if result:
    scores = json.loads(result[0])
    print("Sample: Skor Student ID 8:")
    for key in ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']:
        print(f"  {key:15s}: {scores[key]:.3f}")

conn.close()
