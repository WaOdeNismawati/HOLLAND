import sqlite3
import json

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print('='*60)
print('FINAL VERIFICATION - 10 SISWA PENDIDIKAN')
print('='*60)

# Check all 15 students (ID 8-22)
cursor.execute('''
    SELECT u.id, u.username, tr.top_3_types, tr.recommended_major
    FROM users u
    JOIN test_results tr ON u.id = tr.student_id
    WHERE u.id BETWEEN 8 AND 22
    ORDER BY u.id
''')
results = cursor.fetchall()

print('\nRESULT:\n')
pendidikan_count = 0
pendidikan_students = []
other_students = []

for sid, username, top_3_str, major in results:
    top_3 = json.loads(top_3_str)
    code = ''.join([t[0] for t in top_3])
    
    if major == 'Pendidikan':
        pendidikan_count += 1
        pendidikan_students.append((sid, username, code, major))
        marker = '[PEND]'
    else:
        other_students.append((sid, username, code, major))
        marker = '      '
    
    print(f'{marker} {sid:3d}: {username[:35]:35s} {code:3s} -> {major}')

print(f'\n{"="*60}')
print(f'SUMMARY:')
print(f'  Total siswa dengan rekomendasi Pendidikan: {pendidikan_count}/15')

if pendidikan_count == 10:
    print(f'\n  SUCCESS! Exactly 10 students get Pendidikan recommendation!')
    print(f'\n  10 Siswa Pendidikan:')
    for i, (sid, username, code, major) in enumerate(pendidikan_students, 1):
        print(f'    {i:2d}. {username} (ID {sid})')
    
    print(f'\n  5 Siswa lain:')
    for i, (sid, username, code, major) in enumerate(other_students, 1):
        print(f'    {i}. {username} (ID {sid}) -> {major}')
elif pendidikan_count < 10:
    print(f'\n  Need {10 - pendidikan_count} more Pendidikan recommendations')
else:
    print(f'\n  Need to remove {pendidikan_count - 10} Pendidikan recommendations')
    
print(f'{"="*60}')

conn.close()
