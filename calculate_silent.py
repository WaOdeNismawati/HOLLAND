import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

sys.path.insert(0, 'C:/Users/Admin/OneDrive/Desktop/HOLLAND')

import sqlite3
from utils.holland_calculator import HollandCalculator

# Suppress verbose output dari HollandCalculator
import os
os.environ['PYTHONIOENCODING'] = 'utf-8'

print("="*60)
print("CALCULATING TEST RESULTS")
print("="*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT DISTINCT sa.student_id, u.username
    FROM student_answers sa
    JOIN users u ON sa.student_id = u.id
    WHERE sa.student_id NOT IN (SELECT student_id FROM test_results)
    ORDER BY sa.student_id
''')
students_to_calculate = cursor.fetchall()

print(f"\nTotal siswa: {len(students_to_calculate)}")
print(f"\nProcessing (output suppressed)...")

calculator = HollandCalculator()
success_count = 0
error_count = 0
results = []

for student_id, username in students_to_calculate:
    try:
        # Suppress print output temporarily
        old_stdout = sys.stdout
        sys.stdout = io.StringIO()
        
        result = calculator.process_test_completion(student_id)
        
        # Restore stdout
        sys.stdout = old_stdout
        
        success_count += 1
        results.append({
            'id': student_id,
            'username': username,
            'code': result['holland_code'],
            'major': result['recommended_major']
        })
        if success_count % 10 == 0:
            print(f"Progress: {success_count}/{len(students_to_calculate)}")
    except Exception as e:
        sys.stdout = old_stdout
        error_count += 1
        print(f"Error {student_id}: {str(e)[:100]}")

print(f"\n{'='*60}")
print(f"COMPLETE!")
print(f"Success: {success_count}/{len(students_to_calculate)}")
print(f"Errors: {error_count}")
print(f"\nSample results (first 5):")
for r in results[:5]:
    print(f"  {r['id']}: {r['code']} -> {r['major']}")
print(f"{'='*60}")

conn.close()
