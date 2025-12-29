import streamlit as st
import pandas as pd
import sqlite3
from database.db_manager import DatabaseManager
from utils.auth import check_login, hash_password

# Page config
st.set_page_config(page_title="Manajemen Data", page_icon="🗃️", layout="wide", initial_sidebar_state="collapsed")

from components.upload_csv import (
    upload_csv_student_page,
    upload_csv_soal_page,
    upload_csv_majors_page,
)
from services.read_csv import save_csv_to_db_student_answers

HOLLAND_TYPES = [
    'Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional'
]
MAJOR_TRAITS = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']

# ===============================
# Cek login
# ===============================
check_login()

# ===============================
# Database connection
# ===============================
db_manager = DatabaseManager()
conn = db_manager.get_connection()

if st.session_state.role != 'admin':
    st.error("Akses ditolak! Halaman ini hanya untuk admin.")
    st.stop()


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

    add_expander = st.expander("➕ Tambah Siswa", expanded=False)
    with add_expander:
        with st.form("form_add_student"):
            new_username_input = st.text_input("Username")
            new_full_name_input = st.text_input("Nama Lengkap")
            new_class_name_input = st.text_input("Kelas")
            new_password = st.text_input("Password Baru", type="password")
            submitted_add_student = st.form_submit_button("Simpan Siswa")

        if submitted_add_student:
            new_username = new_username_input.strip()
            new_full_name = new_full_name_input.strip()
            new_class_name = new_class_name_input.strip()
            new_password_value = new_password.strip()
            if not all([new_username, new_full_name, new_password_value]):
                st.warning("Username, nama lengkap, dan password wajib diisi.")
            else:
                try:
                    form_cursor = conn.cursor()
                    form_cursor.execute(
                        '''INSERT INTO users (username, password, role, full_name, class_name)
                           VALUES (?, ?, 'student', ?, ?)''',
                        (new_username, hash_password(new_password_value), new_full_name, new_class_name)
                    )
                    form_cursor.execute("SELECT id, full_name, class_name FROM users WHERE username=?", (new_username,))
                    user_row = form_cursor.fetchone()
                    if user_row:
                        db_manager.ensure_student_profile(form_cursor, user_row[0], new_full_name, new_class_name)
                    conn.commit()
                    st.success("Siswa baru berhasil ditambahkan.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Username sudah digunakan.")
                except Exception as e:
                    st.error(f"Gagal menambahkan siswa: {e}")

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
        student_options = {
            f"{row[0]} - {row[2]} ({row[1]})": row for row in students_data
        }

        with st.expander("✏️ Edit Siswa", expanded=False):
            with st.form("form_edit_student"):
                selected_student_label = st.selectbox("Pilih Siswa untuk Diedit", list(student_options.keys()))
                selected_student = student_options[selected_student_label]
                updated_username = st.text_input("Username Edit", value=selected_student[1])
                updated_full_name = st.text_input("Nama Lengkap Edit", value=selected_student[2])
                updated_class_name = st.text_input("Kelas Edit", value=selected_student[3] or "")
                updated_password = st.text_input("Password Edit (opsional)", type="password")
                submitted_edit_student = st.form_submit_button("Perbarui Siswa")

            if submitted_edit_student:
                if not updated_username.strip() or not updated_full_name.strip():
                    st.warning("Username dan nama lengkap wajib diisi.")
                else:
                    try:
                        form_cursor = conn.cursor()
                        if updated_password:
                            form_cursor.execute(
                                '''UPDATE users SET username=?, full_name=?, class_name=?, password=?
                                   WHERE id=?''',
                                (
                                    updated_username.strip(),
                                    updated_full_name.strip(),
                                    updated_class_name.strip(),
                                    hash_password(updated_password),
                                    selected_student[0]
                                )
                            )
                        else:
                            form_cursor.execute(
                                '''UPDATE users SET username=?, full_name=?, class_name=?
                                   WHERE id=?''',
                                (
                                    updated_username.strip(),
                                    updated_full_name.strip(),
                                    updated_class_name.strip(),
                                    selected_student[0]
                                )
                            )
                        db_manager.update_student_profile(form_cursor, selected_student[0], updated_full_name.strip())
                        conn.commit()
                        st.success("Data siswa berhasil diperbarui.")
                        st.rerun()
                    except sqlite3.IntegrityError:
                        st.error("Username sudah digunakan.")
                    except Exception as e:
                        st.error(f"Gagal memperbarui siswa: {e}")

        with st.expander("🗑️ Hapus Siswa", expanded=False):
            with st.form("form_delete_student"):
                selected_delete_label = st.selectbox("Pilih Siswa untuk Dihapus", list(student_options.keys()), key="delete_student_select")
                confirm_delete_student = st.checkbox("Saya yakin ingin menghapus siswa ini.")
                submitted_delete_student = st.form_submit_button("Hapus Siswa")

            if submitted_delete_student:
                if not confirm_delete_student:
                    st.warning("Centang konfirmasi terlebih dahulu.")
                else:
                    try:
                        student_id = student_options[selected_delete_label][0]
                        form_cursor = conn.cursor()
                        form_cursor.execute("DELETE FROM student_answers WHERE student_id=?", (student_id,))
                        form_cursor.execute("DELETE FROM test_results WHERE student_id=?", (student_id,))
                        form_cursor.execute("DELETE FROM users WHERE id=?", (student_id,))
                        conn.commit()
                        st.success("Siswa berhasil dihapus.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menghapus siswa: {e}")
        # Tombol hapus semua data siswa
        st.warning("⚠️ Hati-hati! Ini akan menghapus seluruh siswa, jawaban, dan hasil tes.")
        if st.button("🗑️ Hapus Semua Data Siswa", key="delete_all_students"):
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM student_answers")  # hapus jawaban
                cursor.execute("DELETE FROM test_results")     # hapus hasil tes
                cursor.execute("DELETE FROM users WHERE role='student'")  # hapus siswa
                conn.commit()
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('student_answers','test_results','users')")
                conn.commit()
                st.success("Seluruh data siswa berhasil dihapus!")
                st.rerun()
            except Exception as e:
                st.error(f"Gagal menghapus seluruh data siswa: {e}")

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

    with st.expander("➕ Tambah Soal", expanded=False):
        with st.form("form_add_question"):
            question_text = st.text_area("Teks Soal Baru")
            question_type = st.selectbox("Tipe Holland Baru", HOLLAND_TYPES)
            difficulty_val = st.number_input("Tingkat Kesulitan (b)", value=0.0, step=0.1)
            discrimination_val = st.number_input("Discrimination (a)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
            guessing_val = st.number_input("Guessing (c)", min_value=0.0, max_value=0.5, value=0.2, step=0.05)
            time_limit_val = st.number_input("Batas Waktu (detik)", min_value=15, max_value=300, value=60, step=5)
            submitted_add_question = st.form_submit_button("Simpan Soal")

        if submitted_add_question:
            if not question_text.strip():
                st.warning("Teks soal wajib diisi.")
            else:
                try:
                    form_cursor = conn.cursor()
                    form_cursor.execute(
                        '''INSERT INTO questions (
                            question_text, holland_type, difficulty, discrimination, guessing, time_limit_seconds
                        ) VALUES (?, ?, ?, ?, ?, ?)''',
                        (
                            question_text.strip(),
                            question_type,
                            float(difficulty_val),
                            float(discrimination_val),
                            float(guessing_val),
                            int(time_limit_val)
                        )
                    )
                    conn.commit()
                    st.success("Soal baru berhasil ditambahkan.")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menambahkan soal: {e}")
                

    # Tampilkan data soal
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, question_text, holland_type, difficulty, discrimination, guessing, time_limit_seconds
        FROM questions ORDER BY id
    ''')
    questions_data = cursor.fetchall()

    if questions_data:
        question_options = {
            f"{row[0]} - {row[1][:50]}..." if len(row[1]) > 50 else f"{row[0]} - {row[1]}": row
            for row in questions_data
        }

        with st.expander("✏️ Edit Soal", expanded=False):
            with st.form("form_edit_question"):
                selected_question_label = st.selectbox("Pilih Soal untuk Diedit", list(question_options.keys()))
                selected_question = question_options[selected_question_label]
                updated_question_text = st.text_area("Teks Soal Edit", value=selected_question[1])
                updated_question_type = st.selectbox(
                    "Tipe Holland Edit",
                    HOLLAND_TYPES,
                    index=HOLLAND_TYPES.index(selected_question[2])
                )
                updated_difficulty = st.number_input(
                    "Tingkat Kesulitan (b) Edit",
                    value=float(selected_question[3] or 0.0),
                    step=0.1
                )
                updated_discrimination = st.number_input(
                    "Discrimination (a) Edit",
                    min_value=0.1,
                    max_value=5.0,
                    value=float(selected_question[4] or 1.0),
                    step=0.1
                )
                updated_guessing = st.number_input(
                    "Guessing (c) Edit",
                    min_value=0.0,
                    max_value=0.5,
                    value=float(selected_question[5] or 0.2),
                    step=0.05
                )
                updated_time_limit = st.number_input(
                    "Batas Waktu (detik) Edit",
                    min_value=15,
                    max_value=300,
                    value=int(selected_question[6] or 60),
                    step=5
                )
                submitted_edit_question = st.form_submit_button("Perbarui Soal")

            if submitted_edit_question:
                if not updated_question_text.strip():
                    st.warning("Teks soal wajib diisi.")
                else:
                    try:
                        form_cursor = conn.cursor()
                        form_cursor.execute(
                            '''UPDATE questions
                               SET question_text=?, holland_type=?, difficulty=?, discrimination=?, guessing=?, time_limit_seconds=?
                               WHERE id=?''',
                            (
                                updated_question_text.strip(),
                                updated_question_type,
                                float(updated_difficulty),
                                float(updated_discrimination),
                                float(updated_guessing),
                                int(updated_time_limit),
                                selected_question[0]
                            )
                        )
                        conn.commit()
                        st.success("Soal berhasil diperbarui.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal memperbarui soal: {e}")

        with st.expander("🗑️ Hapus Soal", expanded=False):
            with st.form("form_delete_question"):
                selected_delete_question_label = st.selectbox(
                    "Pilih Soal untuk Dihapus", list(question_options.keys()), key="delete_question_select"
                )
                confirm_delete_question = st.checkbox("Saya yakin", key="delete_question_confirm")
                submitted_delete_question = st.form_submit_button("Hapus Soal")

            if submitted_delete_question:
                if not confirm_delete_question:
                    st.warning("Centang konfirmasi terlebih dahulu.")
                else:
                    try:
                        question_id = question_options[selected_delete_question_label][0]
                        form_cursor = conn.cursor()
                        form_cursor.execute("DELETE FROM student_answers WHERE question_id=?", (question_id,))
                        form_cursor.execute("DELETE FROM questions WHERE id=?", (question_id,))
                        conn.commit()
                        st.success("Soal berhasil dihapus.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menghapus soal: {e}")

        # Tombol hapus semua soal
        st.warning("⚠️ Hati-hati! Ini akan menghapus seluruh data soal dan jawaban siswa terkait.")
        if st.button("🗑️ Hapus Semua Data Soal", key="delete_all_questions"):
            try:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM student_answers")  # hapus jawaban terkait
                cursor.execute("DELETE FROM questions")  # hapus semua soal
                conn.commit()
                cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('student_answers','questions')")
                conn.commit()
                cursor.execute("VACUUM")
                conn.commit()
                st.success("Seluruh data soal dan jawaban terkait berhasil dihapus!")
                st.rerun()
            except Exception as e:
                st.error(f"Gagal menghapus seluruh data soal: {e}")

        df_questions = pd.DataFrame(
            questions_data,
            columns=['ID', 'Teks Soal', 'Tipe Holland']
        )
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

    with st.expander("➕ Tambah Alternatif", expanded=False):
        with st.form("form_add_major"):
            major_name = st.text_input("Nama Jurusan Baru").strip()
            trait_values = {}
            for trait in MAJOR_TRAITS:
                trait_values[trait] = st.number_input(
                    f"Nilai {trait} (Tambah)",
                    min_value=0.0,
                    max_value=10.0,
                    value=0.0,
                    step=0.1
                )
            submitted_add_major = st.form_submit_button("Simpan Jurusan")

        if submitted_add_major:
            if not major_name:
                st.warning("Nama jurusan wajib diisi.")
            else:
                try:
                    form_cursor = conn.cursor()
                    form_cursor.execute(
                        '''INSERT INTO majors (Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional)
                           VALUES (?, ?, ?, ?, ?, ?, ?)''',
                        (
                            major_name,
                            trait_values['Realistic'],
                            trait_values['Investigative'],
                            trait_values['Artistic'],
                            trait_values['Social'],
                            trait_values['Enterprising'],
                            trait_values['Conventional']
                        )
                    )
                    conn.commit()
                    st.success("Jurusan baru berhasil ditambahkan.")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Nama jurusan sudah terdaftar.")
                except Exception as e:
                    st.error(f"Gagal menambahkan jurusan: {e}")

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

            major_options = {
                f"{row[0]} - {row[1]}": row for row in majors_data
            }

            with st.expander("✏️ Edit Alternatif", expanded=False):
                with st.form("form_edit_major"):
                    selected_major_label = st.selectbox("Pilih Jurusan untuk Diedit", list(major_options.keys()))
                    selected_major = major_options[selected_major_label]
                    updated_major_name = st.text_input("Nama Jurusan Edit", value=selected_major[1])
                    updated_traits = {}
                    for idx, trait in enumerate(MAJOR_TRAITS, start=2):
                        updated_traits[trait] = st.number_input(
                            f"Nilai {trait} (Edit)",
                            min_value=0.0,
                            max_value=10.0,
                            value=float(selected_major[idx] or 0.0),
                            step=0.1
                        )
                    submitted_edit_major = st.form_submit_button("Perbarui Jurusan")

                if submitted_edit_major:
                    if not updated_major_name.strip():
                        st.warning("Nama jurusan wajib diisi.")
                    else:
                        try:
                            form_cursor = conn.cursor()
                            form_cursor.execute(
                                '''UPDATE majors SET Major=?, Realistic=?, Investigative=?, Artistic=?, Social=?, Enterprising=?, Conventional=?
                                   WHERE id=?''',
                                (
                                    updated_major_name.strip(),
                                    updated_traits['Realistic'],
                                    updated_traits['Investigative'],
                                    updated_traits['Artistic'],
                                    updated_traits['Social'],
                                    updated_traits['Enterprising'],
                                    updated_traits['Conventional'],
                                    selected_major[0]
                                )
                            )
                            conn.commit()
                            st.success("Jurusan berhasil diperbarui.")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Nama jurusan sudah terdaftar.")
                        except Exception as e:
                            st.error(f"Gagal memperbarui jurusan: {e}")

            with st.expander("🗑️ Hapus Alternatif", expanded=False):
                with st.form("form_delete_major"):
                    selected_delete_major_label = st.selectbox(
                        "Pilih Jurusan untuk Dihapus", list(major_options.keys()), key="delete_major_select"
                    )
                    confirm_delete_major = st.checkbox("Saya yakin", key="delete_major_confirm")
                    submitted_delete_major = st.form_submit_button("Hapus Jurusan")

                if submitted_delete_major:
                    if not confirm_delete_major:
                        st.warning("Centang konfirmasi terlebih dahulu.")
                    else:
                        try:
                            major_id = major_options[selected_delete_major_label][0]
                            form_cursor = conn.cursor()
                            form_cursor.execute("DELETE FROM majors WHERE id=?", (major_id,))
                            conn.commit()
                            st.success("Jurusan berhasil dihapus.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Gagal menghapus jurusan: {e}")

            # Tombol hapus semua data
            st.warning("⚠️ Hati-hati! Ini akan menghapus seluruh data alternatif jurusan.")
            if st.button("🗑️ Hapus Semua Data Jurusan", type="secondary"):
                try:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM majors")
                    conn.commit()
                    cursor.execute("DELETE FROM sqlite_sequence WHERE name='majors'")
                    conn.commit()
                    st.success("Seluruh data jurusan berhasil dihapus!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Gagal menghapus seluruh data jurusan: {e}")
        else:
            st.info("Belum ada data alternatif (jurusan).")
    except Exception as e:
        st.error(f"Terjadi kesalahan saat memuat data jurusan: {e}")

# =======================
# 📤 UPLOAD CSV JAWABAN
# =======================
st.subheader("📤 Upload Jawaban Siswa (CSV/Excel)")

with st.expander("ℹ️ Format File CSV", expanded=False):
    st.markdown("""
    **Format 1 (Menggunakan student_id):**
```
    student_id,question_id,answer
    1,1,4
    1,2,5
    2,1,3
```
    
    **Format 2 (Menggunakan username):**
```
    username,question_id,answer
    siswa001,1,4
    siswa001,2,5
    siswa002,1,3
```
    
    **Keterangan:**
    - `student_id` atau `username`: ID atau username siswa
    - `question_id`: ID soal (1-60)
    - `answer`: Jawaban siswa (1-5)
    
    **Catatan:**
    - File bisa berformat `.csv`, `.xls`, atau `.xlsx`
    - Jika ada duplikat (student_id + question_id sama), data lama akan diupdate
    - Jawaban harus dalam rentang 1-5
    """)
    
    # Template download
    st.download_button(
        label="📥 Download Template CSV",
        data="student_id,question_id,answer\n1,1,4\n1,2,5\n1,3,3",
        file_name="template_jawaban_siswa.csv",
        mime="text/csv"
    )

with st.form("upload_form_answers"):
    uploaded_file = st.file_uploader(
        "Pilih file CSV/Excel jawaban siswa",
        type=["csv", "xls", "xlsx"],
        help="Upload file berisi jawaban siswa dalam format yang sesuai"
    )
    submit_upload = st.form_submit_button("📤 Upload & Proses", type="primary")

if submit_upload and uploaded_file:
    save_csv_to_db_student_answers(uploaded_file)

st.markdown("---")
conn.close()
