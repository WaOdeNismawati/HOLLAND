import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'C:/Users/Admin/OneDrive/Desktop/HOLLAND')

import sqlite3
from utils.holland_calculator import HollandCalculator
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("="*60)
print("RE-CALCULATE DENGAN PROFIL BARU (EXACT MATCH)")
print("="*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

student_ids = list(range(8, 23))
cursor.execute(f'''
    DELETE FROM test_results 
    WHERE student_id IN ({','.join(['?']*15)})
''', student_ids)
conn.commit()

print(f"\nRe-calculating...\n")

calculator = HollandCalculator()
success_count = 0
pendidikan_count = 0
results = []

for sid in student_ids:
    try:
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        result = calculator.process_test_completion(sid)
        
        sys.stdout = old_stdout
        
        success_count += 1
        is_pendidikan = 'Pendidikan' in result['recommended_major']
        if is_pendidikan:
            pendidikan_count += 1
        
        results.append({
            'id': sid,
            'code': result['holland_code'],
            'major': result['recommended_major']
        })
        
        marker = "??" if is_pendidikan else "? "
        print(f"{marker} ID {sid:3d}: {result['holland_code']} -> {result['recommended_major']}")
        
    except Exception as e:
        sys.stdout = old_stdout
        print(f"? ID {sid:3d}: Error - {str(e)[:100]}")

print(f"\n{'='*60}")
print(f"HASIL:")
print(f"  Total berhasil: {success_count}/15")
print(f"  Rekomendasi 'Pendidikan': {pendidikan_count}/15")
if pendidikan_count < 15:
    print(f"\nJurusan lain yang muncul:")
    other_majors = {}
    for r in results:
        if 'Pendidikan' not in r['major']:
            major = r['major']
            other_majors[major] = other_majors.get(major, 0) + 1
    for major, count in sorted(other_majors.items(), key=lambda x: -x[1]):
        print(f"    {major}: {count}")
print(f"{'='*60}")

conn.close()
