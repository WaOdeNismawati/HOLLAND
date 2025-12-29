import streamlit as st
import pandas as pd
import sqlite3
from database.db_manager import DatabaseManager
from utils.auth import check_login, hash_password
from components.sidebar import render_sidebar
from utils.styles import apply_dark_theme

# Page config
st.set_page_config(page_title="Manajemen Data", page_icon="🗃️", layout="wide", initial_sidebar_state="expanded")

# Apply dark theme
apply_dark_theme()

# Render sidebar
st.session_state.current_page = 'data_management'
render_sidebar()



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

# Tabs untuk berbagai jenis data
tab1, tab2, tab3 = st.tabs(["👥 Data Siswa", "📝 Data Soal", "📚 Data Alternatif (Jurusan)"])

# ===============================
# Tab 1: Data Siswa
# ===============================
with tab1:
    st.subheader("👥 Manajemen Data Siswa")

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
        SELECT sp.student_id, u.username, u.full_name, u.class_name, u.created_at,
               CASE WHEN tr.id IS NOT NULL THEN 'Sudah' ELSE 'Belum' END as status_tes,
               u.id
        FROM users u
        LEFT JOIN test_results tr ON u.id = tr.student_id
        LEFT JOIN student_profiles sp ON u.id = sp.user_id
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
                        user_id = selected_student[6]  # u.id ada di index 6
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
                                    user_id
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
                                    user_id
                                )
                            )
                        db_manager.update_student_profile(form_cursor, user_id, updated_full_name.strip())
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
                        user_id = student_options[selected_delete_label][6]  # u.id ada di index 6
                        form_cursor = conn.cursor()
                        form_cursor.execute("DELETE FROM student_answers WHERE student_id=?", (user_id,))
                        form_cursor.execute("DELETE FROM test_results WHERE student_id=?", (user_id,))
                        form_cursor.execute("DELETE FROM student_profiles WHERE user_id=?", (user_id,))
                        form_cursor.execute("DELETE FROM users WHERE id=?", (user_id,))
                        conn.commit()
                        st.success("Siswa berhasil dihapus.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal menghapus siswa: {e}")

        df_students = pd.DataFrame(students_data, columns=['Student ID', 'Username', 'Nama Lengkap', 'Kelas', 'Tanggal Daftar', 'Status Tes', 'ID'])
        # Hilangkan kolom ID dari tampilan
        df_students_display = df_students.drop(columns=['ID'])
        st.subheader("📋 Daftar Siswa")
        st.dataframe(df_students_display, use_container_width=True)
    else:
        st.info("Belum ada data siswa.")

# ===============================
# Tab 2: Data Soal
# ===============================
with tab2:
    st.subheader("📝 Manajemen Data Soal")

    with st.expander("➕ Tambah Soal", expanded=False):
        with st.form("form_add_question"):
            question_text = st.text_area("Teks Soal Baru")
            question_type = st.selectbox("Tipe Holland Baru", HOLLAND_TYPES)
            submitted_add_question = st.form_submit_button("Simpan Soal")

        if submitted_add_question:
            if not question_text.strip():
                st.warning("Teks soal wajib diisi.")
            else:
                try:
                    form_cursor = conn.cursor()
                    form_cursor.execute(
                        '''INSERT INTO questions (
                            question_text, holland_type
                        ) VALUES (?, ?)''',
                        (
                            question_text.strip(),
                            question_type
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
        SELECT id, question_text, holland_type
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
                submitted_edit_question = st.form_submit_button("Perbarui Soal")

            if submitted_edit_question:
                if not updated_question_text.strip():
                    st.warning("Teks soal wajib diisi.")
                else:
                    try:
                        form_cursor = conn.cursor()
                        form_cursor.execute(
                            '''UPDATE questions
                               SET question_text=?, holland_type=?
                               WHERE id=?''',
                            (
                                updated_question_text.strip(),
                                updated_question_type,
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

conn.close()
