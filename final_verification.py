import sqlite3
import json

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print('='*60)
print('FINAL VERIFICATION')
print('='*60)

# Check the 15 students
cursor.execute('''
    SELECT u.id, u.username, tr.top_3_types, tr.recommended_major, tr.holland_scores
    FROM users u
    JOIN test_results tr ON u.id = tr.student_id
    WHERE u.id BETWEEN 8 AND 22
    ORDER BY u.id
''')
results = cursor.fetchall()

print(f'\n15 Siswa dengan Rekomendasi Pendidikan:\n')
pendidikan_count = 0

for sid, username, top_3_str, major, scores_str in results:
    top_3 = json.loads(top_3_str)
    code = ''.join([t[0] for t in top_3])
    scores = json.loads(scores_str)
    
    if major == 'Pendidikan':
        pendidikan_count += 1
        marker = 'OK'
    else:
        marker = '  '
    
    print(f'{marker} {sid:3d}: {username[:30]:30s} {code} -> {major}')

print(f'\n{"="*60}')
print(f'RESULT: {pendidikan_count}/15 siswa mendapat rekomendasi Pendidikan')

if pendidikan_count == 15:
    print(f'\nSUCCESS! All 15 students successfully assigned to Pendidikan!')
    print(f'\nSample RIASEC profile (Student ID 8):')
    sample_scores = json.loads(results[0][4])
    for key in ['Social', 'Investigative', 'Artistic', 'Enterprising', 'Conventional', 'Realistic']:
        print(f'  {key:15s}: {sample_scores[key]:.3f}')
        
print(f'{"="*60}')

conn.close()
