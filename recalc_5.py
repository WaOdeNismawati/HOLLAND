import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'C:/Users/Admin/OneDrive/Desktop/HOLLAND')

import sqlite3
from utils.holland_calculator import HollandCalculator
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

print('='*60)
print('RE-CALCULATE 5 SISWA DENGAN PROFIL RANDOM')
print('='*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

# Delete old results untuk 5 siswa
student_ids = list(range(18, 23))
cursor.execute(f'''DELETE FROM test_results WHERE student_id IN ({','.join(['?']*5)})''', student_ids)
conn.commit()

calculator = HollandCalculator()
results = []

print('\nCalculating...\n')

for sid in student_ids:
    old_stdout = sys.stdout
    sys.stdout = io.StringIO()
    result = calculator.process_test_completion(sid)
    sys.stdout = old_stdout
    
    holland_code = result['holland_code']
    major = result['recommended_major']
    results.append({'id': sid, 'code': holland_code, 'major': major})
    print(f'ID {sid:3d}: {holland_code} -> {major}')

print(f'\n{"="*60}')
print(f'Done! 5 siswa berhasil di-recalculate')
print(f'{"="*60}')

conn.close()
