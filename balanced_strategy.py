import sqlite3

print('='*60)
print('BALANCED STRATEGY: Match Pendidikan Unique Profile')
print('='*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print('\nPendidikan characteristic: All IAEC sama tinggi (0.474)')
print('Keperawatan: I tinggi (0.667), A rendah (0.333)')
print('\nStrategy: Make I, A, E, C all EQUAL and high')
print('  Social:        5 (raw 50)')
print('  Investigative: 4 (raw 40)')
print('  Artistic:      4 (raw 40)')
print('  Enterprising:  4 (raw 40)')
print('  Conventional:  4 (raw 40)')
print('  Realistic:     2 (raw 20)')
print('\nNormalized: S:1.0, I/A/E/C:0.8 (all equal!), R:0.4')
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
            if holland_type == 'Social':
                answer = 5
            elif holland_type in ['Investigative', 'Artistic', 'Enterprising', 'Conventional']:
                answer = 4
            elif holland_type == 'Realistic':
                answer = 2
            
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
