import streamlit as st
from database.db_manager import DatabaseManager
from utils.auth import check_login, logout
from utils.config import connection
from components.sidebar import render_sidebar
from utils.styles import apply_dark_theme

st.set_page_config(page_title="Dashboard Siswa", page_icon="🎓", layout="wide", initial_sidebar_state="expanded")

# Apply dark theme
apply_dark_theme()

@st.cache_data(ttl=60)
def get_student_progress(user_id):
    """Cache student progress for 60 seconds"""
    conn = connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM test_results WHERE student_id = ?', (user_id,))
    test_completed = cursor.fetchone()[0] > 0
    
    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM student_answers WHERE student_id = ?', (user_id,))
    answered_questions = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'test_completed': test_completed,
        'total_questions': total_questions,
        'answered_questions': answered_questions
    }

# Cek login
check_login()

# Render sidebar
st.session_state.current_page = 'student_dashboard'
render_sidebar()

if st.session_state.role != 'student':
    st.error("Akses ditolak! Halaman ini hanya untuk siswa.")
    st.stop()

# Get cached student progress
progress_data = get_student_progress(st.session_state.user_id)

# Profil siswa
st.subheader("👤 Profil Siswa")

col1, col2 = st.columns(2)

with col1:
    st.info(f"**Nama Lengkap:** {st.session_state.full_name}")

with col2:
    class_name = st.session_state.class_name if st.session_state.class_name else "Tidak ada kelas"
    st.info(f"**Kelas:** {class_name}")

st.markdown("---")

# Status tes
st.subheader("📋 Status Tes")

test_completed = progress_data['test_completed']

col1, col2 = st.columns([1, 2])

with col1:
    if test_completed:
        st.success("✅ **Status:** Sudah Mengerjakan")
    else:
        st.warning("⏳ **Status:** Belum Mengerjakan")

with col2:
    if test_completed:
        st.info("Anda sudah menyelesaikan tes minat bakat. Lihat hasil tes Anda di menu 'Hasil Tes'.")
        if st.button("Lihat Hasil Tes", type="primary"):
            st.switch_page("pages/student_results.py")
    else:
        st.info("Anda belum mengerjakan tes minat bakat. Klik tombol di bawah untuk memulai tes.")
        if st.button("Mulai Tes Minat Bakat", type="primary"):
            st.switch_page("pages/student_test.py")

# Informasi tambahan
st.markdown("---")
st.subheader("ℹ️ Informasi Tes")

with st.expander("Tentang Tes Minat Bakat"):
    st.write("""
    **Tes Minat Bakat Holland** adalah alat penilaian yang membantu Anda memahami:
    
    - **Tipe Kepribadian:** Berdasarkan 6 tipe Holland (RIASEC)
    - **Minat Karier:** Bidang pekerjaan yang sesuai dengan kepribadian Anda
    - **Rekomendasi Jurusan:** Saran jurusan kuliah yang cocok
    
    **6 Tipe Holland:**
    - 🔧 **Realistic:** Praktis, suka bekerja dengan tangan
    - 🔬 **Investigative:** Analitis, suka memecahkan masalah
    - 🎨 **Artistic:** Kreatif, suka berkarya seni
    - 👥 **Social:** Suka membantu dan berinteraksi dengan orang
    - 💼 **Enterprising:** Suka memimpin dan berbisnis
    - 📊 **Conventional:** Terorganisir, suka bekerja dengan data
    """)

with st.expander("Cara Mengerjakan Tes"):
    st.write("""
    1. **Baca setiap pernyataan** dengan teliti
    2. **Pilih jawaban** yang paling sesuai dengan diri Anda:
       - 1 = Sangat Tidak Setuju
       - 2 = Tidak Setuju  
       - 3 = Netral
       - 4 = Setuju
       - 5 = Sangat Setuju
    3. **Jawab dengan jujur** sesuai dengan perasaan dan minat Anda
    4. **Selesaikan semua soal** untuk mendapatkan hasil yang akurat
    """)

# Statistik soal
st.markdown("---")
st.subheader("📈 Progress Tes")

if progress_data['total_questions'] > 0:
    progress = progress_data['answered_questions'] / progress_data['total_questions']
    st.progress(progress)
    st.write(f"Soal dijawab: {progress_data['answered_questions']} dari {progress_data['total_questions']} soal ({progress*100:.1f}%)")
else:
    st.warning("Belum ada soal yang tersedia. Hubungi administrator.")