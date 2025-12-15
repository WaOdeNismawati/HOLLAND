import pandas as pd
import sqlite3
from database.db_manager import DatabaseManager

print("="*70)
print("MANUAL IMPORT TEST - BYPASS STREAMLIT")
print("="*70)

# Read CSV
df = pd.read_csv("data_jawaban_dummy.csv")
print(f"\n1. CSV dibaca: {len(df)} baris")

# Setup database
db = DatabaseManager()
conn = db.get_connection()
cursor = conn.cursor()

# Get valid data from DB
cursor.execute("SELECT id FROM users WHERE role='student'")
valid_students = set([r[0] for r in cursor.fetchall()])

cursor.execute("SELECT id FROM questions")
valid_questions = set([r[0] for r in cursor.fetchall()])

print(f"2. Valid students: {len(valid_students)}")
print(f"3. Valid questions: {len(valid_questions)}")

# Validate CSV data
df["student_id"] = pd.to_numeric(df["student_id"], errors="coerce")
df["question_id"] = pd.to_numeric(df["question_id"], errors="coerce")
df["answer"] = pd.to_numeric(df["answer"], errors="coerce")

# Filter valid data
df = df[df["student_id"].isin(valid_students)]
df = df[df["question_id"].isin(valid_questions)]
df = df[(df["answer"] >= 1) & (df["answer"] <= 5)]

print(f"4. Setelah validasi: {len(df)} baris valid")

# Count before import
cursor.execute("SELECT COUNT(*) FROM student_answers")
before_count = cursor.fetchone()[0]
print(f"5. Jawaban sebelum import: {before_count}")

# Try to insert first 10 rows
print(f"\n6. Mencoba insert 10 baris pertama...")
success = 0
errors = 0

cursor.execute("BEGIN")
for idx, row in df.head(10).iterrows():
    try:
        sid = int(row["student_id"])
        qid = int(row["question_id"])
        ans = int(row["answer"])
        
        # Check existing
        cursor.execute(
            "SELECT id FROM student_answers WHERE student_id=? AND question_id=?",
            (sid, qid)
        )
        existing = cursor.fetchone()
        
        if existing:
            cursor.execute(
                "UPDATE student_answers SET answer=? WHERE student_id=? AND question_id=?",
                (ans, sid, qid)
            )
            print(f"   UPDATE: student={sid}, question={qid}, answer={ans}")
        else:
            cursor.execute(
                "INSERT INTO student_answers (student_id, question_id, answer) VALUES (?, ?, ?)",
                (sid, qid, ans)
            )
            print(f"   INSERT: student={sid}, question={qid}, answer={ans}")
            success += 1
    except Exception as e:
        errors += 1
        print(f"   ERROR row {idx}: {e}")

conn.commit()

# Count after
cursor.execute("SELECT COUNT(*) FROM student_answers")
after_count = cursor.fetchone()[0]

print(f"\n7. Jawaban setelah import: {after_count}")
print(f"8. Berhasil insert: {success}")
print(f"9. Error: {errors}")
print(f"10. Delta: +{after_count - before_count}")

conn.close()
print("\n" + "="*70)
