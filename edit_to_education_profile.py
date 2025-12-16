import sqlite3
import random

print("="*60)
print("EDIT JAWABAN 15 SISWA -> PROFIL PENDIDIKAN (SIA)")
print("="*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

# Target profile: Social tinggi, Investigative &amp; Artistic sedang-tinggi
# Social: 0.79, Investigative: 0.47, Artistic: 0.47

# Get question IDs per holland type
cursor.execute('SELECT id, holland_type FROM questions ORDER BY id')
questions = cursor.fetchall()
question_by_type = {}
for qid, htype in questions:
    if htype not in question_by_type:
        question_by_type[htype] = []
    question_by_type[htype].append(qid)

print(f"\nStrategi jawaban untuk profil SIA:")
print(f"  Social:        jawaban 4-5 (tinggi)")
print(f"  Investigative: jawaban 3-4 (sedang-tinggi)")
print(f"  Artistic:      jawaban 3-4 (sedang-tinggi)")
print(f"  Realistic:     jawaban 1-2 (rendah)")
print(f"  Enterprising:  jawaban 1-2 (rendah)")
print(f"  Conventional:  jawaban 1-2 (rendah)")
print()

# 15 siswa (ID 8-22)
student_ids = list(range(8, 23))
success_count = 0

for sid in student_ids:
    try:
        # Delete old answers
        cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (sid,))
        
        # Insert new answers with SIA profile
        for holland_type, qids in question_by_type.items():
            for qid in qids:
                if holland_type == 'Social':
                    # Social tinggi: mostly 5, some 4
                    answer = random.choice([5, 5, 5, 5, 5, 5, 5, 4, 4, 5])
                elif holland_type == 'Investigative':
                    # Investigative sedang-tinggi: mix 3-4
                    answer = random.choice([3, 3, 4, 4, 4, 3, 4, 3, 4, 4])
                elif holland_type == 'Artistic':
                    # Artistic sedang-tinggi: mix 3-4
                    answer = random.choice([3, 4, 3, 4, 4, 3, 4, 3, 4, 3])
                else:  # Realistic, Enterprising, Conventional
                    # Rendah: mostly 1-2
                    answer = random.choice([1, 2, 1, 2, 2, 1, 2, 1, 2, 1])
                
                cursor.execute('''
                    INSERT INTO student_answers (student_id, question_id, answer)
                    VALUES (?, ?, ?)
                ''', (sid, qid, answer))
        
        conn.commit()
        success_count += 1
        print(f"? Student ID {sid:3d} - Jawaban diupdate")
        
    except Exception as e:
        print(f"? Student ID {sid:3d} - Error: {e}")
        conn.rollback()

print(f"\n{'='*60}")
print(f"Berhasil update: {success_count}/15 siswa")
print(f"{'='*60}")

conn.close()
