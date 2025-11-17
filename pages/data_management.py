import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
from utils.auth import check_login, hash_password
from components.upload_csv import (
    upload_csv_student_page,
    upload_csv_soal_page,
    upload_csv_majors_page
)
from components.sidebar import sidebar
from utils.config import connection

# ===============================
# Cek login
# ===============================
check_login()

# ===============================
# Database connection
# ===============================
db_manager = DatabaseManager()
conn = db_manager.get_connection()
print(st.session_state)

if st.session_state.role != 'admin':
    st.error("Akses ditolak! Halaman ini hanya untuk admin.")
    st.stop()

st.set_page_config(page_title="Manajemen Data", page_icon="🗃️", layout="wide")

# Sidebar
sidebar()

# ===============================
# Main content
# ===============================
st.title("🗃️ Manajemen Data")
st.markdown("---")

# Tabs untuk berbagai jenis data
tab1, tab2, tab3 = st.tabs(["👥 Data Siswa", "📝 Data Soal", "📚 Data Alternatif (Jurusan)"])

# ===============================
# Tab 1: Data Siswa
# ===============================
with tab1:
    st.subheader("👥 Manajemen Data Siswa")

    # Form upload CSV siswa
    upload_csv_student_page()

    # Tampilkan data siswa
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.id, u.username, u.full_name, u.class_name, u.created_at,
               CASE WHEN tr.id IS NOT NULL THEN 'Sudah' ELSE 'Belum' END as status_tes
        FROM users u
        LEFT JOIN test_results tr ON u.id = tr.student_id
        WHERE u.role = 'student'
        ORDER BY u.created_at DESC
    ''')
    students_data = cursor.fetchall()

    if students_data:
        df_students = pd.DataFrame(students_data, columns=['ID', 'Username', 'Nama Lengkap', 'Kelas', 'Tanggal Daftar', 'Status Tes'])
        st.subheader("📋 Daftar Siswa")

        st.dataframe(df_students, use_container_width=True)
    else:
        st.info("Belum ada data siswa.")

# ===============================
# Tab 2: Data Soal
# ===============================
with tab2:
    st.subheader("📝 Manajemen Data Soal")

    # Form upload CSV soal
    upload_csv_soal_page()

    # Tampilkan data soal
    cursor = conn.cursor()
    cursor.execute('SELECT id, question_text, holland_type FROM questions ORDER BY id')
    questions_data = cursor.fetchall()

    if questions_data:
        df_questions = pd.DataFrame(questions_data, columns=['ID', 'Teks Soal', 'Tipe Holland'])
        st.subheader("📋 Daftar Soal")
        st.dataframe(df_questions, use_container_width=True)
    else:
        st.info("Belum ada data soal.")

# ===============================
# Tab 3: Data Alternatif (Jurusan)
# ===============================
with tab3:
    st.subheader("📚 Manajemen Data Alternatif (Jurusan)")

    # Upload CSV jurusan
    upload_csv_majors_page()

    # Tampilkan data jurusan dari tabel majors
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT * FROM majors')
        majors_data = cursor.fetchall()

        if majors_data:
            cols = [desc[0] for desc in cursor.description]
            df_majors = pd.DataFrame(majors_data, columns=cols)
            st.subheader("📋 Daftar Alternatif (Jurusan)")
            st.dataframe(df_majors, use_container_width=True)

            # Tombol hapus semua data
            st.warning("⚠️ Hati-hati! Ini akan menghapus seluruh data alternatif jurusan.")
            if st.button("🗑️ Hapus Semua Data Jurusan", type="secondary"):
                cursor.execute("DELETE FROM majors")
                conn.commit()
                st.success("Seluruh data jurusan berhasil dihapus!")
                st.rerun()
        else:
            st.info("Belum ada data alternatif (jurusan).")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data jurusan: {e}")

conn.close()
