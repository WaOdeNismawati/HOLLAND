import sqlite3
conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()
cursor.execute('SELECT id, username FROM users WHERE role=?', ('student',))
students = cursor.fetchall()
cursor.execute('SELECT DISTINCT student_id FROM student_answers')
answered = [r[0] for r in cursor.fetchall()]
not_answered = [s for s in students if s[0] not in answered]
print('Total siswa:', len(students))
print('Sudah menjawab:', len(answered))
print('Belum menjawab:', len(not_answered))
print('\nSiswa yang belum menjawab:')
for s in not_answered:
    print(f'{s[0]}: {s[1]}')
conn.close()
