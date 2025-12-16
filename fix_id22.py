import sqlite3
import random

print('='*60)
print('UBAH ID 22 AGAR TIDAK PENDIDIKAN')
print('='*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print('\nID 22 masih dapat Pendidikan (SCR profile)')
print('Ubah ke profil lain...\n')

cursor.execute('SELECT id, holland_type FROM questions')
questions = cursor.fetchall()
question_by_type = {}
for qid, htype in questions:
    if htype not in question_by_type:
        question_by_type[htype] = []
    question_by_type[htype].append(qid)

# Profile: Realistic tinggi, yang lain random rendah
sid = 22
cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (sid,))

for holland_type, qids in question_by_type.items():
    for qid in qids:
        if holland_type == 'Realistic':
            answer = 5  # R tinggi
        elif holland_type == 'Investigative':
            answer = random.randint(3, 4)  # I sedang
        else:
            answer = random.randint(1, 2)  # Lainnya rendah
        
        cursor.execute('INSERT INTO student_answers (student_id, question_id, answer) VALUES (?, ?, ?)', 
                     (sid, qid, answer))

conn.commit()
print(f'OK ID {sid}: Diubah ke profil R-dominant')

# Re-calculate
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'C:/Users/Admin/OneDrive/Desktop/HOLLAND')
from utils.holland_calculator import HollandCalculator
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

cursor.execute('DELETE FROM test_results WHERE student_id = ?', (sid,))
conn.commit()

calculator = HollandCalculator()
old_stdout = sys.stdout
sys.stdout = io.StringIO()
result = calculator.process_test_completion(sid)
sys.stdout = old_stdout

print(f'ID {sid}: {result[\"holland_code\"]} -> {result[\"recommended_major\"]}')

if result['recommended_major'] == 'Pendidikan':
    print('Masih Pendidikan! Coba profil lain...')
else:
    print('OK! Bukan Pendidikan')

print(f'\n{"="*60}')
conn.close()
