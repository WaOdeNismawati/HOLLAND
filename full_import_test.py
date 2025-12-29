import pandas as pd
import sqlite3

print("="*70)
print("FULL IMPORT TEST - 300 ROWS")
print("="*70)

df = pd.read_csv("data_jawaban_dummy.csv")
print(f"\n[1] CSV loaded: {len(df)} rows")

conn = sqlite3.connect("exam_system.db")
cursor = conn.cursor()

# Check before
cursor.execute("SELECT COUNT(*) FROM student_answers")
before = cursor.fetchone()[0]
print(f"[2] Before: {before} answers")

# Get valid IDs
cursor.execute("SELECT id FROM users WHERE role='student'")
valid_students = set([r[0] for r in cursor.fetchall()])

cursor.execute("SELECT id FROM questions")
valid_questions = set([r[0] for r in cursor.fetchall()])

# Validate
df = df[df["student_id"].isin(valid_students)]
df = df[df["question_id"].isin(valid_questions)]
df = df[(df["answer"] >= 1) & (df["answer"] <= 5)]
print(f"[3] Valid rows: {len(df)}")

# Import ALL
print(f"\n[4] Importing ALL {len(df)} rows...")
success = 0
updated = 0
errors = 0

cursor.execute("BEGIN")
for idx, row in df.iterrows():
    try:
        sid = int(row["student_id"])
        qid = int(row["question_id"])
        ans = int(row["answer"])
        
        cursor.execute(
            "SELECT id FROM student_answers WHERE student_id=? AND question_id=?",
            (sid, qid)
        )
        exists = cursor.fetchone()
        
        if exists:
            cursor.execute(
                "UPDATE student_answers SET answer=? WHERE student_id=? AND question_id=?",
                (ans, sid, qid)
            )
            updated += 1
        else:
            cursor.execute(
                "INSERT INTO student_answers (student_id, question_id, answer, created_at) VALUES (?, ?, ?, datetime('now','+8 hours'))",
                (sid, qid, ans)
            )
            success += 1
        
        if (idx + 1) % 50 == 0:
            print(f"    Progress: {idx + 1}/{len(df)}...")
            
    except Exception as e:
        errors += 1

conn.commit()

# Check after
cursor.execute("SELECT COUNT(*) FROM student_answers")
after = cursor.fetchone()[0]

# Check students
print(f"\n[5] Students with answers:")
for sid in sorted(df["student_id"].unique()):
    cursor.execute("SELECT COUNT(*) FROM student_answers WHERE student_id=?", (int(sid),))
    count = cursor.fetchone()[0]
    cursor.execute("SELECT full_name FROM users WHERE id=?", (int(sid),))
    name = cursor.fetchone()[0]
    print(f"    ID {sid}: {name} ({count} answers)")

print(f"\n[6] FINAL RESULTS:")
print(f"    Before:   {before}")
print(f"    After:    {after}")
print(f"    Delta:    +{after - before}")
print(f"    Inserted: {success}")
print(f"    Updated:  {updated}")
print(f"    Errors:   {errors}")

if success > 0 or updated > 0:
    print(f"\n[SUCCESS] Import worked! Total processed: {success + updated}")
else:
    print(f"\n[FAILED] No data was processed")

conn.close()
print("="*70)
