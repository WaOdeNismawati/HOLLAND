import sqlite3
import random

print("="*60)
print("RE-EDIT JAWABAN -> MATCH EXACT PROFILE PENDIDIKAN")
print("="*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

# Pendidikan profile (normalized):
# S:0.79 (highest), I:0.47, A:0.47, R:0.32, E:0.47, C:0.47
# Target student normalized scores:
# S:1.0, I:0.60, A:0.60, R:0.40, E:0.60, C:0.60

print(f"\nNEW Strategy - Match Pendidikan profile exactly:")
print(f"  Social:        5 (sangat tinggi) -> raw ~50")
print(f"  Investigative: 3 (sedang) -> raw ~30")  
print(f"  Artistic:      3 (sedang) -> raw ~30")
print(f"  Enterprising:  3 (sedang) -> raw ~30")
print(f"  Conventional:  3 (sedang) -> raw ~30")
print(f"  Realistic:     2 (rendah) -> raw ~20")
print(f"\nIni akan membuat S dominan, sisanya seimbang\n")

# Get question IDs per holland type
cursor.execute('SELECT id, holland_type FROM questions ORDER BY id')
questions = cursor.fetchall()
question_by_type = {}
for qid, htype in questions:
    if htype not in question_by_type:
        question_by_type[htype] = []
    question_by_type[htype].append(qid)

student_ids = list(range(8, 23))
success_count = 0

for sid in student_ids:
    try:
        cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (sid,))
        
        for holland_type, qids in question_by_type.items():
            for qid in qids:
                if holland_type == 'Social':
                    # Social SANGAT tinggi: semua 5
                    answer = 5
                elif holland_type in ['Investigative', 'Artistic', 'Enterprising', 'Conventional']:
                    # Sedang: mostly 3
                    answer = 3
                elif holland_type == 'Realistic':
                    # Rendah: mostly 2
                    answer = 2
                
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
