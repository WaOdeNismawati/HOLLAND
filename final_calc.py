import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'C:/Users/Admin/OneDrive/Desktop/HOLLAND')

import sqlite3
from utils.holland_calculator import HollandCalculator
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("="*60)
print("FINAL RE-CALCULATE")
print("="*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

student_ids = list(range(8, 23))
cursor.execute(f'''DELETE FROM test_results WHERE student_id IN ({','.join(['?']*15)})''', student_ids)
conn.commit()

calculator = HollandCalculator()
success_count = 0
pendidikan_count = 0
results = []

print(f"\nCalculating...\n")

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
        
        results.append({
            'id': sid,
            'code': result['holland_code'],
            'major': result['recommended_major']
        })
        
        marker = "??" if is_pendidikan else "  "
        print(f"{marker} ID {sid:3d}: {result['holland_code']} -> {result['recommended_major']}")
        
    except Exception as e:
        sys.stdout = old_stdout
        print(f"? ID {sid:3d}: Error")

print(f"\n{'='*60}")
print(f"HASIL AKHIR:")
print(f"  Total: {success_count}/15")
print(f"  Pendidikan: {pendidikan_count}/15 ({'? SUCCESS' if pendidikan_count == 15 else 'need adjustment'})")

if pendidikan_count < 15:
    print(f"\n  Jurusan lain:")
    other = {}
    for r in results:
        if r['major'] != 'Pendidikan':
            other[r['major']] = other.get(r['major'], 0) + 1
    for m, c in sorted(other.items(), key=lambda x: -x[1]):
        print(f"    {m}: {c}")
print(f"{'='*60}")

conn.close()
