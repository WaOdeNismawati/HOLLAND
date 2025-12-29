import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'C:/Users/Admin/OneDrive/Desktop/HOLLAND')

import sqlite3
from utils.holland_calculator import HollandCalculator
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

print('='*60)
print('CALCULATE WITH PURE SOCIAL PROFILE')
print('='*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

student_ids = list(range(8, 23))
cursor.execute(f'''DELETE FROM test_results WHERE student_id IN ({','.join(['?']*15)})''', student_ids)
conn.commit()

calculator = HollandCalculator()
success_count = 0
pendidikan_count = 0
results = []

print('\nCalculating...\n')

for sid in student_ids:
    try:
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        result = calculator.process_test_completion(sid)
        sys.stdout = old_stdout
        
        success_count += 1
        is_pendidikan = result['recommended_major'] == 'Pendidikan'
        if is_pendidikan:
            pendidikan_count += 1
        
        holland_code = result['holland_code']
        major = result['recommended_major']
        
        results.append({'id': sid, 'code': holland_code, 'major': major})
        
        marker = 'PEND' if is_pendidikan else '    '
        print(f'{marker} ID {sid:3d}: {holland_code} -> {major}')
        
    except Exception as e:
        sys.stdout = old_stdout
        print(f'ERR ID {sid:3d}')

print('\n' + '='*60)
print('HASIL:')
print(f'  Total: {success_count}/15')
print(f'  Pendidikan: {pendidikan_count}/15')

if pendidikan_count == 15:
    print('\n  SUCCESS! All 15 students get Pendidikan!')
else:
    other = {}
    for r in results:
        m = r['major']
        other[m] = other.get(m, 0) + 1
    print('\n  Distribution:')
    for m, c in sorted(other.items(), key=lambda x: -x[1]):
        print(f'    {m}: {c}')
        
print('='*60)

conn.close()
