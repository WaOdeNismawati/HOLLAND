import sqlite3
import csv
from datetime import datetime

conn = sqlite3.connect("exam_system.db")
cursor = conn.cursor()

print("BACKUP DATA JURUSAN")
print("="*80)

cursor.execute("SELECT * FROM majors")
rows = cursor.fetchall()
columns = [desc[0] for desc in cursor.description]

backup_filename = f"majors_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(backup_filename, "w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(columns)
    writer.writerows(rows)

print(f"[OK] Backup created: {backup_filename}")
print(f"[OK] Total majors: {len(rows)}")

conn.close()
