import sqlite3

print('='*60)
print('PURE SOCIAL STRATEGY')
print('='*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print('\nMembuat profil:')
print('  Social: 5 (max)')
print('  ALL OTHERS: 1 (min)')
print()

cursor.execute('SELECT id, holland_type FROM questions')
questions = cursor.fetchall()
question_by_type = {}
for qid, htype in questions:
    if htype not in question_by_type:
        question_by_type[htype] = []
    question_by_type[htype].append(qid)

student_ids = list(range(8, 23))
success = 0

for sid in student_ids:
    cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (sid,))
    
    for holland_type, qids in question_by_type.items():
        for qid in qids:
            answer = 5 if holland_type == 'Social' else 1
            cursor.execute('INSERT INTO student_answers (student_id, question_id, answer) VALUES (?, ?, ?)', 
                         (sid, qid, answer))
    conn.commit()
    success += 1
    if success % 5 == 0:
        print(f'Progress: {success}/15')

print(f'\n{"="*60}')
print(f'Updated: {success}/15')
print(f'{"="*60}')
conn.close()
