import sqlite3
import json

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print("="*60)
print("PILIH 15 SISWA UNTUK DIUBAH KE PROFIL PENDIDIKAN")
print("="*60)

# Ambil 15 siswa dari yang dummy (ID 8-22)
cursor.execute('''
    SELECT u.id, u.username, tr.recommended_major
    FROM users u
    JOIN test_results tr ON u.id = tr.student_id
    WHERE u.id BETWEEN 8 AND 22
    ORDER BY u.id
''')
selected_students = cursor.fetchall()

print(f"\n15 Siswa yang akan diubah:\n")
for sid, username, current_major in selected_students:
    print(f"{sid:3d}: {username:40s} -> {current_major}")

# Get question distribution
cursor.execute('''
    SELECT holland_type, GROUP_CONCAT(id) as question_ids
    FROM questions
    GROUP BY holland_type
''')
question_groups = cursor.fetchall()

print(f"\n{'='*60}")
print("Distribusi Pertanyaan:")
for holland_type, ids in question_groups:
    id_list = ids.split(',')
    print(f"{holland_type:15s}: {len(id_list)} pertanyaan")

conn.close()
