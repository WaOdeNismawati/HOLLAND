import streamlit as st
from database.db_manager import DatabaseManager
from utils.auth import check_login
from utils.holland_calculator import HollandCalculator

# Cek login
check_login()

if st.session_state.role != 'student':
    st.error("Akses ditolak! Halaman ini hanya untuk siswa.")
    st.stop()

st.set_page_config(page_title="Tes Minat Bakat", page_icon="📝", layout="wide")

# Sidebar
with st.sidebar:
    st.title("📝 Tes Minat Bakat")
    st.write(f"Siswa: {st.session_state.full_name}")
    
    if st.button("🏠 Kembali ke Dashboard"):
        st.switch_page("pages/student_dashboard.py")

# Main content
st.title("📝 Tes Minat Bakat Holland")
st.markdown("---")

# Database connection
db_manager = DatabaseManager()
conn = db_manager.get_connection()
cursor = conn.cursor()

# Cek apakah siswa sudah mengerjakan tes
cursor.execute('''
    SELECT COUNT(*) FROM test_results WHERE student_id = ?
''', (st.session_state.user_id,))

if cursor.fetchone()[0] > 0:
    st.warning("⚠️ Anda sudah menyelesaikan tes ini sebelumnya.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Lihat Hasil Tes"):
            st.switch_page("pages/student_results.py")
    with col2:
        if st.button("Kembali ke Dashboard"):
            st.switch_page("pages/student_dashboard.py")
    st.stop()

# Ambil semua soal
cursor.execute('''
    SELECT id, question_text, holland_type FROM questions ORDER BY id
''')
questions = cursor.fetchall()

if not questions:
    st.error("Tidak ada soal yang tersedia. Hubungi administrator.")
    st.stop()

# Ambil jawaban yang sudah ada (jika ada)
cursor.execute('''
    SELECT question_id, answer FROM student_answers WHERE student_id = ?
''', (st.session_state.user_id,))
existing_answers = dict(cursor.fetchall())

st.info(f"📋 Total soal: {len(questions)} | Skala: 1 (Sangat Tidak Setuju) - 5 (Sangat Setuju)")

# Form untuk tes
with st.form("test_form"):
    st.subheader("Jawab setiap pernyataan sesuai dengan diri Anda:")
    
    answers = {}
    
    for i, (question_id, question_text, holland_type) in enumerate(questions, 1):
        st.write(f"**{i}. {question_text}**")
        
        # Nilai default dari jawaban sebelumnya atau 3 (netral)
        default_value = existing_answers.get(question_id, 3)
        
        answer = st.radio(
            f"Pilih jawaban untuk soal {i}:",
            options=[1, 2, 3, 4, 5],
            format_func=lambda x: {
                1: "1 - Sangat Tidak Setuju",
                2: "2 - Tidak Setuju", 
                3: "3 - Netral",
                4: "4 - Setuju",
                5: "5 - Sangat Setuju"
            }[x],
            index=default_value - 1,
            key=f"q_{question_id}",
            horizontal=True
        )
        
        answers[question_id] = answer
        st.markdown("---")
    
    # Tombol submit
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        submit_button = st.form_submit_button("🚀 Selesaikan Tes", type="primary", use_container_width=True)

# Proses jawaban
if submit_button:
    try:
        # Hapus jawaban lama jika ada
        cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (st.session_state.user_id,))
        
        # Simpan jawaban baru
        for question_id, answer in answers.items():
            cursor.execute('''
                INSERT INTO student_answers (student_id, question_id, answer)
                VALUES (?, ?, ?)
            ''', (st.session_state.user_id, question_id, answer))
        
        conn.commit()
        
        # Hitung hasil menggunakan Holland Calculator
        calculator = HollandCalculator()
        result = calculator.process_test_completion(st.session_state.user_id)
        
        st.success("🎉 Tes berhasil diselesaikan!")
        st.balloons()
        
        # Tampilkan hasil singkat
        st.subheader("📊 Hasil Tes Anda:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**3 Tipe Kepribadian Teratas:**")
            for i, holland_type in enumerate(result['top_3_types'], 1):
                st.write(f"{i}. {holland_type}")
        
        with col2:
            st.write("**Rekomendasi Jurusan:**")
            st.success(result['recommended_major'])
        
        # Tombol untuk melihat hasil lengkap
        if st.button("Lihat Hasil Lengkap", type="primary"):
            st.switch_page("pages/student_results.py")
            
    except Exception as e:
        st.error(f"Terjadi kesalahan: {str(e)}")
        conn.rollback()

conn.close()