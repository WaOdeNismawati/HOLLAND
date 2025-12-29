import sqlite3

conn = sqlite3.connect("exam_system.db")
cursor = conn.cursor()

majors = ["Teknologi Pangan", "Statistika", "Teknik Informatika", "Farmasi", "Matematika"]

print("Database profiles for top candidates:\n")
for major in majors:
    cursor.execute("SELECT Realistic, Investigative, Artistic, Social, Enterprising, Conventional FROM majors WHERE Major = ?", (major,))
    row = cursor.fetchone()
    if row:
        print(f"{major:30s}")
        print(f"  R={row[0]:.2f} I={row[1]:.2f} A={row[2]:.2f} S={row[3]:.2f} E={row[4]:.2f} C={row[5]:.2f}")
        i_c_sum = row[1] + row[5]
        print(f"  I+C sum: {i_c_sum:.2f}")
        print()

conn.close()
