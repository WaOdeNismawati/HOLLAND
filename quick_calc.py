import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'C:/Users/Admin/OneDrive/Desktop/HOLLAND')

import sqlite3
from utils.holland_calculator import HollandCalculator
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

student_ids = list(range(8, 23))
cursor.execute(f'''DELETE FROM test_results WHERE student_id IN ({','.join(['?']*15)})''', student_ids)
conn.commit()

calculator = HollandCalculator()
results = []

print('Calculating...\n')

for sid in student_ids:
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    result = calculator.process_test_completion(sid)
    sys.stdout = old_stdout
    
    holland_code = result['holland_code']
    major = result['recommended_major']
    results.append({'id': sid, 'code': holland_code, 'major': major})
    print(f'ID {sid:3d}: {holland_code} -> {major}')

pendidikan_count = sum(1 for r in results if r['major'] == 'Pendidikan')

print(f'\nPendidikan: {pendidikan_count}/15')

if pendidikan_count < 15:
    dist = {}
    for r in results:
        m = r['major']
        dist[m] = dist.get(m, 0) + 1
    for m, c in sorted(dist.items(), key=lambda x: -x[1]):
        print(f'{m}: {c}')

conn.close()
