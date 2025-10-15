import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
from utils.auth import check_login, hash_password

# Cek login
check_login()

if st.session_state.role != 'admin':
    st.error("Akses ditolak! Halaman ini hanya untuk admin.")
    st.stop()

st.set_page_config(page_title="Manajemen Data", page_icon="🗃️", layout="wide")

# Sidebar
with st.sidebar:
    st.title("🗃️ Manajemen Data")
    st.write(f"Admin: {st.session_state.full_name}")
    
    if st.button("🏠 Dashboard Admin"):
        st.switch_page("pages/admin_dashboard.py")

# Main content
st.title("🗃️ Manajemen Data")
st.markdown("---")

# Tabs untuk berbagai jenis data
tab1, tab2, tab3 = st.tabs(["👥 Data Siswa", "📝 Data Soal", "🎓 Data Jurusan (Alternatif)"])

# Database connection
db_manager = DatabaseManager()

# Tab 1: Data Siswa
with tab1:
    st.subheader("👥 Manajemen Data Siswa")
    
    # Form tambah siswa
    with st.expander("➕ Tambah Siswa Baru"):
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("Username")
                new_password = st.text_input("Password", type="password")
            
            with col2:
                new_fullname = st.text_input("Nama Lengkap")
                new_class = st.text_input("Kelas")
            
            if st.form_submit_button("Tambah Siswa"):
                if new_username and new_password and new_fullname:
                    conn = db_manager.get_connection()
                    cursor = conn.cursor()
                    
                    try:
                        # Cek username sudah ada atau belum
                        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (new_username,))
                        if cursor.fetchone()[0] > 0:
                            st.error("Username sudah digunakan!")
                        else:
                            # Hash password
                            hashed_password = hash_password(new_password)
                            
                            cursor.execute('''
                                INSERT INTO users (username, password, role, full_name, class_name)
                                VALUES (?, ?, ?, ?, ?)
                            ''', (new_username, hashed_password, 'student', new_fullname, new_class))
                            
                            conn.commit()
                            st.success("Siswa berhasil ditambahkan!")
                            st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    finally:
                        conn.close()
                else:
                    st.error("Mohon isi semua field yang wajib!")
    
    # Tampilkan data siswa
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT u.id, u.username, u.full_name, u.class_name, u.created_at,
               (SELECT COUNT(*) FROM test_results WHERE student_id = u.id) as test_count
        FROM users u
        WHERE u.role = 'student'
        ORDER BY u.created_at DESC
    ''')
    
    students_data = cursor.fetchall()
    
    if students_data:
        df_students = pd.DataFrame(students_data, 
                                  columns=['ID', 'Username', 'Nama Lengkap', 'Kelas', 'Tanggal Daftar', 'Jumlah Tes'])
        
        st.subheader("📋 Daftar Siswa")
        
        # Filter
        filter_class = st.selectbox("Filter Kelas",
                                       options=['Semua'] + list(df_students['Kelas'].dropna().unique()))
        
        # Apply filters
        filtered_df = df_students.copy()
        if filter_class != 'Semua':
            filtered_df = filtered_df[filtered_df['Kelas'] == filter_class]
        
        st.dataframe(filtered_df, use_container_width=True)
        
        # Edit/Delete siswa
        st.subheader("✏️ Edit/Hapus Siswa")
        
        student_options = {f"{row[2]} ({row[1]})": row[0] for row in students_data}
        selected_student = st.selectbox("Pilih Siswa", options=list(student_options.keys()))
        
        if selected_student:
            student_id = student_options[selected_student]
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✏️ Edit Siswa", use_container_width=True):
                    st.session_state.edit_student_id = student_id
            
            with col2:
                if st.button("🗑️ Hapus Siswa", use_container_width=True, type="secondary"):
                    st.session_state.confirm_delete_student_id = student_id

            if st.session_state.get('confirm_delete_student_id') == student_id:
                st.warning(f"Yakin ingin menghapus siswa **{selected_student}** dan semua datanya?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Ya, Hapus", use_container_width=True):
                        cursor.execute('DELETE FROM test_results WHERE student_id = ?', (student_id,))
                        cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (student_id,))
                        cursor.execute('DELETE FROM users WHERE id = ?', (student_id,))
                        conn.commit()
                        st.success("Siswa berhasil dihapus!")
                        del st.session_state.confirm_delete_student_id
                        st.rerun()
                with c2:
                    if st.button("❌ Batal", use_container_width=True):
                        del st.session_state.confirm_delete_student_id
                        st.rerun()

            # Form edit siswa
            if st.session_state.get('edit_student_id') == student_id:
                cursor.execute('SELECT username, full_name, class_name FROM users WHERE id = ?', (student_id,))
                current_data = cursor.fetchone()
                
                with st.form("edit_student_form"):
                    st.write("**Edit Data Siswa**")
                    edit_username = st.text_input("Username", value=current_data[0])
                    edit_fullname = st.text_input("Nama Lengkap", value=current_data[1])
                    edit_class = st.text_input("Kelas", value=current_data[2] or "")
                    edit_password = st.text_input("Password Baru (kosongkan jika tidak diubah)", type="password")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Simpan"):
                            try:
                                if edit_password:
                                    hashed_password = hash_password(edit_password)
                                    cursor.execute('''
                                        UPDATE users SET username = ?, full_name = ?, class_name = ?, password = ?
                                        WHERE id = ?
                                    ''', (edit_username, edit_fullname, edit_class, hashed_password, student_id))
                                else:
                                    cursor.execute('''
                                        UPDATE users SET username = ?, full_name = ?, class_name = ?
                                        WHERE id = ?
                                    ''', (edit_username, edit_fullname, edit_class, student_id))
                                
                                conn.commit()
                                st.success("Data siswa berhasil diupdate!")
                                del st.session_state.edit_student_id
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col2:
                        if st.form_submit_button("❌ Batal"):
                            del st.session_state.edit_student_id
                            st.rerun()
    
    else:
        st.info("Belum ada data siswa.")
    
    conn.close()

# Tab 2: Data Soal
with tab2:
    st.subheader("📝 Manajemen Data Soal")
    
    # Form tambah soal
    with st.expander("➕ Tambah Soal Baru"):
        with st.form("add_question_form"):
            new_question = st.text_area("Teks Soal")
            new_holland_type = st.selectbox("Tipe Holland", 
                                          options=['Realistic', 'Investigative', 'Artistic', 
                                                  'Social', 'Enterprising', 'Conventional'])
            
            if st.form_submit_button("Tambah Soal"):
                if new_question:
                    conn = db_manager.get_connection()
                    cursor = conn.cursor()
                    
                    try:
                        cursor.execute('''
                            INSERT INTO questions (question_text, holland_type)
                            VALUES (?, ?)
                        ''', (new_question, new_holland_type))
                        
                        conn.commit()
                        st.success("Soal berhasil ditambahkan!")
                        st.rerun()
                    
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    finally:
                        conn.close()
                else:
                    st.error("Mohon isi teks soal!")
    
    # Tampilkan data soal
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, question_text, holland_type FROM questions ORDER BY id')
    questions_data = cursor.fetchall()
    
    if questions_data:
        df_questions = pd.DataFrame(questions_data, columns=['ID', 'Teks Soal', 'Tipe Holland'])
        
        st.subheader("📋 Daftar Soal")
        
        # Filter berdasarkan tipe Holland
        filter_holland = st.selectbox("Filter Tipe Holland", 
                                     options=['Semua'] + ['Realistic', 'Investigative', 'Artistic', 
                                                          'Social', 'Enterprising', 'Conventional'], key="filter_q_holland")
        
        if filter_holland != 'Semua':
            filtered_questions = df_questions[df_questions['Tipe Holland'] == filter_holland]
        else:
            filtered_questions = df_questions
        
        st.dataframe(filtered_questions, use_container_width=True)
        
        # Edit/Delete soal
        st.subheader("✏️ Edit/Hapus Soal")
        
        question_options = {f"Soal {row[0]}: {row[1][:50]}...": row[0] for row in questions_data}
        selected_question = st.selectbox("Pilih Soal", options=list(question_options.keys()), key="select_q")
        
        if selected_question:
            question_id = question_options[selected_question]
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✏️ Edit Soal", use_container_width=True):
                    st.session_state.edit_question_id = question_id
            
            with col2:
                if st.button("🗑️ Hapus Soal", use_container_width=True, type="secondary"):
                    st.session_state.confirm_delete_question_id = question_id

            if st.session_state.get('confirm_delete_question_id') == question_id:
                st.warning(f"Yakin ingin menghapus soal #{question_id}?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Ya, Hapus", use_container_width=True, key=f"confirm_del_q_{question_id}"):
                        cursor.execute('DELETE FROM student_answers WHERE question_id = ?', (question_id,))
                        cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
                        conn.commit()
                        st.success("Soal berhasil dihapus!")
                        del st.session_state.confirm_delete_question_id
                        st.rerun()
                with c2:
                    if st.button("❌ Batal", use_container_width=True, key=f"cancel_del_q_{question_id}"):
                        del st.session_state.confirm_delete_question_id
                        st.rerun()
            
            # Form edit soal
            if st.session_state.get('edit_question_id') == question_id:
                cursor.execute('SELECT question_text, holland_type FROM questions WHERE id = ?', (question_id,))
                current_question = cursor.fetchone()
                
                with st.form("edit_question_form"):
                    st.write("**Edit Soal**")
                    edit_question_text = st.text_area("Teks Soal", value=current_question[0])
                    edit_holland_type = st.selectbox("Tipe Holland", 
                                                   options=['Realistic', 'Investigative', 'Artistic', 
                                                           'Social', 'Enterprising', 'Conventional'],
                                                   index=['Realistic', 'Investigative', 'Artistic', 
                                                         'Social', 'Enterprising', 'Conventional'].index(current_question[1]))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.form_submit_button("💾 Simpan"):
                            try:
                                cursor.execute('''
                                    UPDATE questions SET question_text = ?, holland_type = ?
                                    WHERE id = ?
                                ''', (edit_question_text, edit_holland_type, question_id))
                                
                                conn.commit()
                                st.success("Soal berhasil diupdate!")
                                del st.session_state.edit_question_id
                                st.rerun()
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    
                    with col2:
                        if st.form_submit_button("❌ Batal"):
                            del st.session_state.edit_question_id
                            st.rerun()
    
    else:
        st.info("Belum ada data soal.")
    
    conn.close()

# Tab 3: Data Jurusan (Alternatif)
with tab3:
    st.subheader("🎓 Manajemen Data Jurusan (Alternatif ANP)")

    with st.expander("➕ Tambah Jurusan Baru"):
        with st.form("add_alternative_form", clear_on_submit=True):
            new_major_name = st.text_input("Nama Jurusan")
            st.write("Bobot RIASEC (0.0 - 1.0):")
            cols = st.columns(3)
            with cols[0]:
                new_r = st.number_input("Realistic", min_value=0.0, max_value=1.0, step=0.1, format="%.1f", key="new_r")
                new_i = st.number_input("Investigative", min_value=0.0, max_value=1.0, step=0.1, format="%.1f", key="new_i")
            with cols[1]:
                new_a = st.number_input("Artistic", min_value=0.0, max_value=1.0, step=0.1, format="%.1f", key="new_a")
                new_s = st.number_input("Social", min_value=0.0, max_value=1.0, step=0.1, format="%.1f", key="new_s")
            with cols[2]:
                new_e = st.number_input("Enterprising", min_value=0.0, max_value=1.0, step=0.1, format="%.1f", key="new_e")
                new_c = st.number_input("Conventional", min_value=0.0, max_value=1.0, step=0.1, format="%.1f", key="new_c")

            if st.form_submit_button("Tambah Jurusan"):
                if new_major_name:
                    conn = db_manager.get_connection()
                    cursor = conn.cursor()
                    try:
                        cursor.execute(
                            "INSERT INTO alternatives (major_name, realistic, investigative, artistic, social, enterprising, conventional) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (new_major_name, new_r, new_i, new_a, new_s, new_e, new_c)
                        )
                        conn.commit()
                        st.success(f"Jurusan '{new_major_name}' berhasil ditambahkan!")
                        st.rerun()
                    except conn.IntegrityError:
                        st.error(f"Jurusan dengan nama '{new_major_name}' sudah ada.")
                    except Exception as e:
                        st.error(f"Error: {str(e)}")
                    finally:
                        conn.close()
                else:
                    st.error("Nama jurusan tidak boleh kosong!")

    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, major_name, realistic, investigative, artistic, social, enterprising, conventional FROM alternatives ORDER BY major_name")
    alternatives_data = cursor.fetchall()

    if alternatives_data:
        df_alternatives = pd.DataFrame(alternatives_data, columns=['ID', 'Nama Jurusan', 'R', 'I', 'A', 'S', 'E', 'C'])
        st.subheader("📋 Daftar Jurusan (Alternatif)")
        st.dataframe(df_alternatives, use_container_width=True, hide_index=True)

        st.subheader("✏️ Edit/Hapus Jurusan")
        major_options = {row[1]: row[0] for row in alternatives_data}
        selected_major_name = st.selectbox("Pilih Jurusan", options=list(major_options.keys()), key="select_major_edit")

        if selected_major_name:
            major_id = major_options[selected_major_name]

            col1, col2 = st.columns(2)
            with col1:
                if st.button("✏️ Edit Jurusan", key=f"edit_major_{major_id}", use_container_width=True):
                    st.session_state.edit_major_id = major_id
                    st.rerun()
            with col2:
                if st.button("🗑️ Hapus Jurusan", key=f"delete_major_{major_id}", use_container_width=True, type="secondary"):
                    st.session_state.confirm_delete_major_id = major_id
                    st.rerun()

            if st.session_state.get('confirm_delete_major_id') == major_id:
                st.warning(f"Yakin ingin menghapus **{selected_major_name}**?")
                c1, c2 = st.columns(2)
                with c1:
                    if st.button("✅ Ya, Hapus", use_container_width=True):
                        cursor.execute('DELETE FROM alternatives WHERE id = ?', (major_id,))
                        conn.commit()
                        st.success("Jurusan berhasil dihapus!")
                        del st.session_state.confirm_delete_major_id
                        st.rerun()
                with c2:
                    if st.button("❌ Batal", use_container_width=True):
                        del st.session_state.confirm_delete_major_id
                        st.rerun()

            if st.session_state.get('edit_major_id') == major_id:
                cursor.execute("SELECT major_name, realistic, investigative, artistic, social, enterprising, conventional FROM alternatives WHERE id = ?", (major_id,))
                current_major = cursor.fetchone()
                with st.form(f"edit_major_form_{major_id}"):
                    st.write(f"**Edit Jurusan: {current_major[0]}**")
                    edit_major_name = st.text_input("Nama Jurusan", value=current_major[0])
                    cols_edit = st.columns(3)
                    with cols_edit[0]:
                        edit_r = st.number_input("Realistic", value=float(current_major[1]), min_value=0.0, max_value=1.0, step=0.1, format="%.1f")
                        edit_i = st.number_input("Investigative", value=float(current_major[2]), min_value=0.0, max_value=1.0, step=0.1, format="%.1f")
                    with cols_edit[1]:
                        edit_a = st.number_input("Artistic", value=float(current_major[3]), min_value=0.0, max_value=1.0, step=0.1, format="%.1f")
                        edit_s = st.number_input("Social", value=float(current_major[4]), min_value=0.0, max_value=1.0, step=0.1, format="%.1f")
                    with cols_edit[2]:
                        edit_e = st.number_input("Enterprising", value=float(current_major[5]), min_value=0.0, max_value=1.0, step=0.1, format="%.1f")
                        edit_c = st.number_input("Conventional", value=float(current_major[6]), min_value=0.0, max_value=1.0, step=0.1, format="%.1f")

                    btn_cols = st.columns(2)
                    with btn_cols[0]:
                        if st.form_submit_button("💾 Simpan"):
                            try:
                                cursor.execute(
                                    "UPDATE alternatives SET major_name=?, realistic=?, investigative=?, artistic=?, social=?, enterprising=?, conventional=? WHERE id=?",
                                    (edit_major_name, edit_r, edit_i, edit_a, edit_s, edit_e, edit_c, major_id)
                                )
                                conn.commit()
                                st.success("Data jurusan berhasil diupdate!")
                                del st.session_state.edit_major_id
                                st.rerun()
                            except conn.IntegrityError:
                                st.error(f"Nama jurusan '{edit_major_name}' sudah ada.")
                            except Exception as e:
                                st.error(f"Error: {str(e)}")
                    with btn_cols[1]:
                        if st.form_submit_button("❌ Batal"):
                            del st.session_state.edit_major_id
                            st.rerun()
    else:
        st.info("Belum ada data jurusan (alternatif). Silakan tambahkan.")

    conn.close()