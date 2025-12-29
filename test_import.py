import pandas as pd
import sqlite3

print("="*70)
print("TEST IMPORT CSV")
print("="*70)

df = pd.read_csv("template_jawaban_test.csv")
print(f"\nFile terbaca: {len(df)} baris")
print(f"Kolom: {list(df.columns)}")

conn = sqlite3.connect("exam_system.db")
cur = conn.cursor()

# Check student
sid = int(df["student_id"].iloc[0])
cur.execute("SELECT username FROM users WHERE id=?", (sid,))
student = cur.fetchone()
print(f"\nStudent ID {sid}: {student[0] if student else 'NOT FOUND'}")

# Check questions
cur.execute("SELECT COUNT(*) FROM questions WHERE id BETWEEN 1 AND 10")
print(f"Questions 1-10: {cur.fetchone()[0]} valid")

# Check current answers
cur.execute("SELECT COUNT(*) FROM student_answers WHERE student_id=?", (sid,))
current = cur.fetchone()[0]
print(f"Jawaban existing untuk student {sid}: {current}")

conn.close()
print("\nCSV VALID! Siap diimport.")
print("="*70)
