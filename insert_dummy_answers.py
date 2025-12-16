import sqlite3
import random

print("="*60)
print("INSERTING DUMMY ANSWERS FOR STUDENTS")
print("="*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

# Get students yang belum menjawab
cursor.execute('SELECT id, username FROM users WHERE role=?', ('student',))
students = cursor.fetchall()
cursor.execute('SELECT DISTINCT student_id FROM student_answers')
answered = [r[0] for r in cursor.fetchall()]
not_answered = [s for s in students if s[0] not in answered]

# Get all question IDs
cursor.execute('SELECT id FROM questions ORDER BY id')
question_ids = [r[0] for r in cursor.fetchall()]

print(f"\nTotal siswa belum menjawab: {len(not_answered)}")
print(f"Total pertanyaan: {len(question_ids)}")
print(f"\nMulai insert jawaban dummy...\n")

success_count = 0
for student_id, username in not_answered:
    try:
        # Generate random answers (1-5) untuk setiap pertanyaan
        for question_id in question_ids:
            answer = random.randint(1, 5)
            cursor.execute('''
                INSERT INTO student_answers (student_id, question_id, answer)
                VALUES (?, ?, ?)
            ''', (student_id, question_id, answer))
        
        conn.commit()
        success_count += 1
        print(f"? {student_id}: {username} - {len(question_ids)} jawaban diinsert")
    except Exception as e:
        print(f"? {student_id}: {username} - Error: {e}")
        conn.rollback()

print(f"\n{'='*60}")
print(f"SELESAI!")
print(f"Berhasil insert: {success_count}/{len(not_answered)} siswa")
print(f"Total jawaban diinsert: {success_count * len(question_ids)}")
print(f"{'='*60}")

conn.close()
