import sqlite3

conn = sqlite3.connect("exam_system.db")
cursor = conn.cursor()

print("="*80)
print("ANALISIS PROFIL JURUSAN - Checking Major Profiles")
print("="*80)

# Get profiles for problematic majors
majors = ["Hubungan Masyarakat", "Perhotelan", "Teknik Informatika", 
          "Desain Komunikasi Visual", "Psikologi"]

print("\nMajor Profiles in Database:\n")
print(f"{'Major':<35} {'R':>5} {'I':>5} {'A':>5} {'S':>5} {'E':>5} {'C':>5} {'Sum':>6}")
print("-"*80)

for major in majors:
    cursor.execute("""
        SELECT Realistic, Investigative, Artistic, Social, Enterprising, Conventional
        FROM majors WHERE Major = ?
    """, (major,))
    
    row = cursor.fetchone()
    if row:
        total = sum(row)
        print(f"{major:<35} {row[0]:5.2f} {row[1]:5.2f} {row[2]:5.2f} {row[3]:5.2f} {row[4]:5.2f} {row[5]:5.2f} {total:6.2f}")

# Get all majors with high total scores
print("\n" + "="*80)
print("All Majors sorted by TOTAL score (sum of all RIASEC):")
print("="*80)

cursor.execute("""
    SELECT Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional,
           (Realistic + Investigative + Artistic + Social + Enterprising + Conventional) as total
    FROM majors
    ORDER BY total DESC
    LIMIT 15
""")

print(f"\n{'Major':<35} {'R':>5} {'I':>5} {'A':>5} {'S':>5} {'E':>5} {'C':>5} {'Sum':>6}")
print("-"*80)

for row in cursor.fetchall():
    print(f"{row[0]:<35} {row[1]:5.2f} {row[2]:5.2f} {row[3]:5.2f} {row[4]:5.2f} {row[5]:5.2f} {row[6]:5.2f} {row[7]:6.2f}")

conn.close()
