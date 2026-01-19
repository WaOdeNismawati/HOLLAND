import sqlite3

conn = sqlite3.connect('exam_system.db')
cursor = conn.cursor()

# Update test_results yang menggunakan PG PAUD
cursor.execute('UPDATE test_results SET recommended_major = ? WHERE recommended_major = ?', 
               ('Pendidikan Guru Anak Usia Dini', 'PG PAUD'))
print(f'Updated {cursor.rowcount} test results from PG PAUD')

# Hapus PG PAUD dari majors (karena sudah ada Pendidikan Guru Anak Usia Dini)
cursor.execute('DELETE FROM majors WHERE Major = ?', ('PG PAUD',))
print(f'Deleted PG PAUD from majors')

# Cek jika ada PGSD, update juga
cursor.execute('UPDATE test_results SET recommended_major = ? WHERE recommended_major = ?',
               ('Pendidikan Guru Sekolah Dasar', 'PGSD'))
print(f'Updated {cursor.rowcount} test results from PGSD')

cursor.execute('DELETE FROM majors WHERE Major = ?', ('PGSD',))
print(f'Deleted PGSD from majors (if existed)')

conn.commit()

# Verifikasi
cursor.execute('SELECT Major FROM majors ORDER BY Major')
print('\nSemua jurusan terkait pendidikan:')
for r in cursor.fetchall():
    if 'Guru' in r[0] or 'PAUD' in r[0] or 'PGSD' in r[0] or 'Pendidikan' in r[0]:
        print(f'  - {r[0]}')

conn.close()
print('\nDone!')
