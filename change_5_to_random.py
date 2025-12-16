import sqlite3
import random

print('='*60)
print('UBAH 5 SISWA TERAKHIR KE PROFIL RANDOM')
print('='*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print('\n10 siswa pertama (ID 8-17): tetap Pendidikan')
print('5 siswa terakhir (ID 18-22): ubah ke profil random\n')

cursor.execute('SELECT id, holland_type FROM questions')
questions = cursor.fetchall()
question_by_type = {}
for qid, htype in questions:
    if htype not in question_by_type:
        question_by_type[htype] = []
    question_by_type[htype].append(qid)

# 5 siswa yang akan diubah
student_ids_to_change = list(range(18, 23))
success = 0

for sid in student_ids_to_change:
    cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (sid,))
    
    # Generate random profile
    for holland_type, qids in question_by_type.items():
        for qid in qids:
            # Random answer 1-5
            answer = random.randint(1, 5)
            cursor.execute('INSERT INTO student_answers (student_id, question_id, answer) VALUES (?, ?, ?)', 
                         (sid, qid, answer))
    
    conn.commit()
    success += 1
    print(f'OK ID {sid}: Jawaban diubah ke profil random')

print(f'\n{"="*60}')
print(f'Updated: {success}/5 siswa')
print(f'{"="*60}')
conn.close()
