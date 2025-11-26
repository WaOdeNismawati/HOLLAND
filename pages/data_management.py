import streamlit as st
import pandas as pd
from database.db_manager import DatabaseManager
from utils.auth import check_login, hash_password
from utils.navbar_components import show_top_navbar

# Page config
st.set_page_config(page_title="Manajemen Data", page_icon="🗃️", layout="wide", initial_sidebar_state="collapsed")

# Cek login
check_login()

if st.session_state.role != 'admin':
    st.error("Akses ditolak! Halaman ini hanya untuk admin.")
    st.stop()

# Show navbar
show_top_navbar(st.session_state.role)

# Main content
st.title("🗃️ Manajemen Data")
st.markdown("---")

# Tabs untuk berbagai jenis data
tab1, tab2 = st.tabs(["👥 Data Siswa", "📝 Data Soal"])

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
               CASE WHEN tr.id IS NOT NULL THEN 'Sudah' ELSE 'Belum' END as status_tes
        FROM users u
        LEFT JOIN test_results tr ON u.id = tr.student_id
        WHERE u.role = 'student'
        ORDER BY u.created_at DESC
    ''')
    
    students_data = cursor.fetchall()
    
    if students_data:
        df_students = pd.DataFrame(students_data, 
                                  columns=['ID', 'Username', 'Nama Lengkap', 'Kelas', 'Tanggal Daftar', 'Status Tes'])
        
        st.subheader("📋 Daftar Siswa")
        
        # Filter
        col1, col2 = st.columns(2)
        with col1:
            filter_class = st.selectbox("Filter Kelas", 
                                       options=['Semua'] + list(df_students['Kelas'].dropna().unique()))
        with col2:
            filter_status = st.selectbox("Filter Status Tes", 
                                        options=['Semua', 'Sudah', 'Belum'])
        
        # Apply filters
        filtered_df = df_students.copy()
        if filter_class != 'Semua':
            filtered_df = filtered_df[filtered_df['Kelas'] == filter_class]
        if filter_status != 'Semua':
            filtered_df = filtered_df[filtered_df['Status Tes'] == filter_status]
        
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
                    if st.session_state.get('confirm_delete_student') == student_id:
                        # Hapus siswa dan data terkait
                        cursor.execute('DELETE FROM test_results WHERE student_id = ?', (student_id,))
                        cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (student_id,))
                        cursor.execute('DELETE FROM users WHERE id = ?', (student_id,))
                        conn.commit()
                        st.success("Siswa berhasil dihapus!")
                        if 'confirm_delete_student' in st.session_state:
                            del st.session_state.confirm_delete_student
                        st.rerun()
                    else:
                        st.session_state.confirm_delete_student = student_id
                        st.warning("Klik sekali lagi untuk konfirmasi hapus!")
            
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
                                                          'Social', 'Enterprising', 'Conventional'])
        
        if filter_holland != 'Semua':
            filtered_questions = df_questions[df_questions['Tipe Holland'] == filter_holland]
        else:
            filtered_questions = df_questions
        
        st.dataframe(filtered_questions, use_container_width=True)
        
        # Edit/Delete soal
        st.subheader("✏️ Edit/Hapus Soal")
        
        question_options = {f"Soal {row[0]}: {row[1][:50]}...": row[0] for row in questions_data}
        selected_question = st.selectbox("Pilih Soal", options=list(question_options.keys()))
        
        if selected_question:
            question_id = question_options[selected_question]
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("✏️ Edit Soal", use_container_width=True):
                    st.session_state.edit_question_id = question_id
            
            with col2:
                if st.button("🗑️ Hapus Soal", use_container_width=True, type="secondary"):
                    if st.session_state.get('confirm_delete_question') == question_id:
                        # Hapus soal dan jawaban terkait
                        cursor.execute('DELETE FROM student_answers WHERE question_id = ?', (question_id,))
                        cursor.execute('DELETE FROM questions WHERE id = ?', (question_id,))
                        conn.commit()
                        st.success("Soal berhasil dihapus!")
                        if 'confirm_delete_question' in st.session_state:
                            del st.session_state.confirm_delete_question
                        st.rerun()
                    else:
                        st.session_state.confirm_delete_question = question_id
                        st.warning("Klik sekali lagi untuk konfirmasi hapus!")
            
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