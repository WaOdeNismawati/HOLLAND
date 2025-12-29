import sqlite3
import random

print("="*60)
print("FINAL STRATEGY: MINIMIZE I, BOOST A/E/C")
print("="*60)

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

print(f"\nTarget: Match Pendidikan profile")
print(f"  Pendidikan: S:0.789 (highest), I:0.474, A:0.474, E:0.474, C:0.474, R:0.316")
print(f"\nJawaban Strategy:")
print(f"  Social:        5 (max) -> raw ~50")
print(f"  Artistic:      4 (tinggi-sedang) -> raw ~40")
print(f"  Enterprising:  4 (tinggi-sedang) -> raw ~40")
print(f"  Conventional:  3 (sedang) -> raw ~30")
print(f"  Investigative: 2 (rendah) -> raw ~20")
print(f"  Realistic:     2 (rendah) -> raw ~20")
print(f"\nHasil normalisasi (S=1.0):")
print(f"  S:1.0, A:0.8, E:0.8, C:0.6, I:0.4, R:0.4")
print()

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
                    answer = 5
                elif holland_type in ['Artistic', 'Enterprising']:
                    answer = 4
                elif holland_type == 'Conventional':
                    answer = 3
                elif holland_type in ['Investigative', 'Realistic']:
                    answer = 2
                
                cursor.execute('''
                    INSERT INTO student_answers (student_id, question_id, answer)
                    VALUES (?, ?, ?)
                ''', (sid, qid, answer))
        
        conn.commit()
        success_count += 1
        print(f"? Student ID {sid:3d}")
        
    except Exception as e:
        print(f"? Student ID {sid:3d} - Error: {e}")
        conn.rollback()

print(f"\n{'='*60}")
print(f"Update: {success_count}/15 siswa")
print(f"{'='*60}")

conn.close()
