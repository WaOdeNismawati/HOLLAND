import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, 'C:/Users/Admin/OneDrive/Desktop/HOLLAND')

import sqlite3
from utils.holland_calculator import HollandCalculator
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("="*60)
print("RE-CALCULATE 15 SISWA DENGAN PROFIL BARU")
print("="*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

# Delete old results untuk 15 siswa
student_ids = list(range(8, 23))
cursor.execute(f'''
    DELETE FROM test_results 
    WHERE student_id IN ({','.join(['?']*15)})
''', student_ids)
conn.commit()

print(f"\nOld results deleted for 15 students")
print(f"Re-calculating...\n")

calculator = HollandCalculator()
success_count = 0
results = []

for sid in student_ids:
    try:
        # Suppress verbose output
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        result = calculator.process_test_completion(sid)
        
        sys.stdout = old_stdout
        
        success_count += 1
        results.append({
            'id': sid,
            'code': result['holland_code'],
            'major': result['recommended_major']
        })
        print(f"? ID {sid:3d}: {result['holland_code']} -> {result['recommended_major']}")
        
    except Exception as e:
        sys.stdout = old_stdout
        print(f"? ID {sid:3d}: Error - {str(e)[:100]}")

# Count Pendidikan recommendations
pendidikan_count = sum(1 for r in results if 'Pendidikan' in r['major'])

print(f"\n{'='*60}")
print(f"HASIL:")
print(f"  Berhasil: {success_count}/15")
print(f"  Rekomendasi 'Pendidikan': {pendidikan_count}/15")
print(f"{'='*60}")

conn.close()
