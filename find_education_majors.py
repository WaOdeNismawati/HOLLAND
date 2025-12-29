import sqlite3
import json

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print("="*60)
print("MENCARI JURUSAN PENDIDIKAN")
print("="*60)

# Cari jurusan yang mengandung kata 'Pendidikan'
cursor.execute('''
    SELECT Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional
    FROM majors
    WHERE Major LIKE '%Pendidikan%'
    ORDER BY Major
''')
education_majors = cursor.fetchall()

print(f"\nTotal jurusan pendidikan: {len(education_majors)}\n")

for major_data in education_majors:
    major = major_data[0]
    r, i, a, s, e, c = major_data[1:]
    print(f"{major}")
    print(f"  R:{r:.2f} I:{i:.2f} A:{a:.2f} S:{s:.2f} E:{e:.2f} C:{c:.2f}")
    # Temukan top 3 RIASEC
    riasec_dict = {'R': r, 'I': i, 'A': a, 'S': s, 'E': e, 'C': c}
    sorted_riasec = sorted(riasec_dict.items(), key=lambda x: x[1], reverse=True)
    top_3 = ''.join([code for code, _ in sorted_riasec[:3]])
    print(f"  Top 3: {top_3}")
    print()

conn.close()
