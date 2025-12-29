import sys
sys.path.insert(0, 'C:/Users/Admin/OneDrive/Desktop/HOLLAND')

import sqlite3
from utils.holland_calculator import HollandCalculator

print("="*60)
print("CALCULATING TEST RESULTS FOR ALL STUDENTS WITH DUMMY ANSWERS")
print("="*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

# Get students yang sudah punya jawaban tapi belum punya hasil
cursor.execute('''
    SELECT DISTINCT sa.student_id, u.username
    FROM student_answers sa
    JOIN users u ON sa.student_id = u.id
    WHERE sa.student_id NOT IN (SELECT student_id FROM test_results)
    ORDER BY sa.student_id
''')
students_to_calculate = cursor.fetchall()

print(f"\nTotal siswa yang perlu dihitung: {len(students_to_calculate)}")
print(f"\nMulai perhitungan...\n")

calculator = HollandCalculator()
success_count = 0
error_count = 0

for student_id, username in students_to_calculate:
    try:
        # Hitung skor RIASEC dan rekomendasi jurusan
        result = calculator.process_test_completion(student_id)
        success_count += 1
        print(f"? [{success_count}/{len(students_to_calculate)}] {student_id}: {username}")
        print(f"   Holland Code: {result['holland_code']} -> {result['recommended_major']}")
    except Exception as e:
        error_count += 1
        print(f"? {student_id}: {username} - Error: {e}")

print(f"\n{'='*60}")
print(f"SELESAI!")
print(f"Berhasil: {success_count}/{len(students_to_calculate)} siswa")
print(f"Error: {error_count}/{len(students_to_calculate)} siswa")
print(f"{'='*60}")

conn.close()
