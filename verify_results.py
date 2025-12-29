import sqlite3

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print("="*60)
print("VERIFICATION REPORT")
print("="*60)

# Total siswa
cursor.execute('SELECT COUNT(*) FROM users WHERE role=?', ('student',))
total_students = cursor.fetchone()[0]

# Siswa dengan jawaban
cursor.execute('SELECT COUNT(DISTINCT student_id) FROM student_answers')
students_with_answers = cursor.fetchone()[0]

# Siswa dengan hasil
cursor.execute('SELECT COUNT(*) FROM test_results')
students_with_results = cursor.fetchone()[0]

print(f"\nTotal siswa: {total_students}")
print(f"Siswa dengan jawaban: {students_with_answers}")
print(f"Siswa dengan hasil tes: {students_with_results}")
print(f"\nCoverage: {students_with_results}/{total_students} ({students_with_results/total_students*100:.1f}%)")

# Sample hasil
cursor.execute('''
    SELECT u.username, tr.top_3_types, tr.recommended_major
    FROM test_results tr
    JOIN users u ON tr.student_id = u.id
    ORDER BY tr.student_id
    LIMIT 10
''')
results = cursor.fetchall()

print(f"\n{'='*60}")
print("SAMPLE RESULTS (10 siswa)")
print("="*60)
for username, top_3, major in results:
    import json
    top_3_list = json.loads(top_3)
    code = ''.join([t[0] for t in top_3_list])
    print(f"{username}: {code} -> {major}")

print(f"{'='*60}")

conn.close()
