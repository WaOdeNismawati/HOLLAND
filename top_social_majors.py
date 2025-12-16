import sqlite3

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print("="*60)
print("TOP 10 JURUSAN DENGAN SOCIAL TERTINGGI")
print("="*60)

cursor.execute('''
    SELECT Major, Social, Realistic, Investigative, Artistic, Enterprising, Conventional
    FROM majors
    ORDER BY Social DESC
    LIMIT 10
''')
majors = cursor.fetchall()

print()
for major, s, r, i, a, e, c in majors:
    print(f"{major:30s} S:{s:.3f} | R:{r:.3f} I:{i:.3f} A:{a:.3f} E:{e:.3f} C:{c:.3f}")
    riasec_dict = {'R': r, 'I': i, 'A': a, 'S': s, 'E': e, 'C': c}
    sorted_riasec = sorted(riasec_dict.items(), key=lambda x: x[1], reverse=True)
    top_3 = ''.join([code for code, val in sorted_riasec[:3]])
    print(f"{'':30s} Top 3: {top_3}\n")

conn.close()
