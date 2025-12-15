import pandas as pd
import sqlite3

print("="*70)
print("VALIDASI FILE: data_jawaban_dummy.csv")
print("="*70)

df = pd.read_csv("data_jawaban_dummy.csv")

print(f"\nFile Info:")
print(f"  Total baris: {len(df)}")
print(f"  Kolom: {list(df.columns)}")
print(f"  Students unik: {df['student_id'].nunique()}")
print(f"  Questions unik: {df['question_id'].nunique()}")

print(f"\nDistribusi Jawaban:")
print(df["answer"].value_counts().sort_index())

# Validate with database
conn = sqlite3.connect("exam_system.db")
cur = conn.cursor()

print(f"\nValidasi Student IDs:")
for sid in sorted(df["student_id"].unique()):
    cur.execute("SELECT username, full_name FROM users WHERE id=?", (int(sid),))
    student = cur.fetchone()
    if student:
        print(f"  [OK] ID {sid}: {student[1]}")
    else:
        print(f"  [ERROR] ID {sid}: TIDAK DITEMUKAN!")

# Check questions
cur.execute("SELECT COUNT(*) FROM questions")
total_questions = cur.fetchone()[0]
print(f"\nValidasi Questions:")
print(f"  Database: {total_questions} soal")
print(f"  CSV: {df['question_id'].nunique()} soal unique")
print(f"  Range: {df['question_id'].min()}-{df['question_id'].max()}")

# Check answers
invalid = df[(df["answer"] < 1) | (df["answer"] > 5)]
print(f"\nValidasi Answers:")
print(f"  Range: {df['answer'].min()}-{df['answer'].max()}")
print(f"  Invalid: {len(invalid)} rows")

conn.close()

print("\n" + "="*70)
if len(invalid) == 0:
    print("STATUS: CSV VALID! Siap untuk diimport via Streamlit!")
else:
    print("STATUS: CSV INVALID! Ada jawaban di luar range 1-5")
print("="*70)
