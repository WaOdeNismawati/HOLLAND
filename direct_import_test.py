import pandas as pd
import sqlite3

print("="*70)
print("DIRECT SQL IMPORT TEST")
print("="*70)

# Read CSV
df = pd.read_csv("data_jawaban_dummy.csv")
print(f"\n[1] CSV loaded: {len(df)} rows")

# Connect directly
conn = sqlite3.connect("exam_system.db")
cursor = conn.cursor()

# Check current state
cursor.execute("SELECT COUNT(*) FROM student_answers")
before = cursor.fetchone()[0]
print(f"[2] Current answers in DB: {before}")

# Get valid IDs
cursor.execute("SELECT id FROM users WHERE role='student'")
valid_students = set([r[0] for r in cursor.fetchall()])
print(f"[3] Valid students: {len(valid_students)}")

cursor.execute("SELECT id FROM questions")
valid_questions = set([r[0] for r in cursor.fetchall()])
print(f"[4] Valid questions: {len(valid_questions)}")

# Validate data
print(f"\n[5] Validating CSV data...")
df_clean = df.copy()
df_clean = df_clean[df_clean["student_id"].isin(valid_students)]
df_clean = df_clean[df_clean["question_id"].isin(valid_questions)]
df_clean = df_clean[(df_clean["answer"] >= 1) & (df_clean["answer"] <= 5)]
print(f"    Valid rows: {len(df_clean)}/{len(df)}")

# Try importing FIRST 5 rows only
print(f"\n[6] Attempting to import first 5 rows...")
success = 0
updated = 0
errors = []

for idx, row in df_clean.head(5).iterrows():
    try:
        sid = int(row["student_id"])
        qid = int(row["question_id"])
        ans = int(row["answer"])
        
        # Check if exists
        cursor.execute(
            "SELECT id FROM student_answers WHERE student_id=? AND question_id=?",
            (sid, qid)
        )
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute(
                "UPDATE student_answers SET answer=?, created_at=datetime('now','+8 hours') WHERE student_id=? AND question_id=?",
                (ans, sid, qid)
            )
            updated += 1
            print(f"    [UPDATE] S:{sid} Q:{qid} A:{ans}")
        else:
            cursor.execute(
                "INSERT INTO student_answers (student_id, question_id, answer, created_at) VALUES (?, ?, ?, datetime('now','+8 hours'))",
                (sid, qid, ans)
            )
            success += 1
            print(f"    [INSERT] S:{sid} Q:{qid} A:{ans}")
            
    except Exception as e:
        errors.append(str(e))
        print(f"    [ERROR] Row {idx}: {e}")

# Commit
conn.commit()

# Check after
cursor.execute("SELECT COUNT(*) FROM student_answers")
after = cursor.fetchone()[0]

print(f"\n[7] Results:")
print(f"    Before: {before}")
print(f"    After: {after}")
print(f"    Delta: +{after - before}")
print(f"    Inserted: {success}")
print(f"    Updated: {updated}")
print(f"    Errors: {len(errors)}")

if after > before:
    print(f"\n[SUCCESS] Import WORKED! Data berhasil masuk ke database!")
else:
    print(f"\n[FAILED] Import FAILED! Data tidak masuk.")
    if errors:
        print(f"Errors: {errors}")

conn.close()
print("="*70)
