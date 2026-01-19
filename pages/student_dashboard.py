import streamlit as st
from database.db_manager import DatabaseManager
from utils.auth import check_login
from utils.config import connection
from utils.styles import apply_dark_theme, render_sidebar, page_header

# Page config
st.set_page_config(page_title="Dashboard Siswa", page_icon="🎓", layout="wide")

# Apply dark theme
apply_dark_theme()

# Check access
check_login()
if st.session_state.role != 'student':
    st.error("Akses ditolak! Halaman ini hanya untuk siswa.")
    st.stop()

# Render sidebar
render_sidebar(current_page="student_dashboard")

# Database connection
conn = connection()
cursor = conn.cursor()

# Page header
page_header("Dashboard Siswa", f"Selamat datang, {st.session_state.full_name}")

# Profile cards
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="card">
        <p style="color: #64748b; font-size: 0.875rem; margin: 0;">👤 Nama Lengkap</p>
        <p style="color: #1e3a8a; font-size: 1.25rem; font-weight: 600; margin: 0.5rem 0 0 0;">
            {st.session_state.full_name}
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    class_name = st.session_state.class_name if st.session_state.class_name else "Tidak ada kelas"
    st.markdown(f"""
    <div class="card">
        <p style="color: #64748b; font-size: 0.875rem; margin: 0;">🏫 Kelas</p>
        <p style="color: #1e3a8a; font-size: 1.25rem; font-weight: 600; margin: 0.5rem 0 0 0;">
            {class_name}
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Test status
cursor.execute('SELECT COUNT(*) FROM test_results WHERE student_id = ?', (st.session_state.user_id,))
test_completed = cursor.fetchone()[0] > 0

st.markdown("#### 📋 Status Tes")

if test_completed:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #10b981, #059669); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
        <h3 style="color: white; margin: 0;">✅ Tes Selesai!</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
            Anda sudah menyelesaikan tes minat bakat. Lihat hasil tes Anda di menu Hasil Tes.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("📊 Lihat Hasil Tes", type="primary", use_container_width=True):
        st.switch_page("pages/student_results.py")
else:
    st.markdown("""
    <div style="background: linear-gradient(135deg, #f59e0b, #d97706); padding: 1.5rem; border-radius: 12px; margin-bottom: 1rem;">
        <h3 style="color: white; margin: 0;">⏳ Belum Mengerjakan Tes</h3>
        <p style="color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0;">
            Anda belum mengerjakan tes minat bakat. Klik tombol di bawah untuk memulai.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("✏️ Mulai Tes Minat Bakat", type="primary", use_container_width=True):
        st.switch_page("pages/student_test.py")

# Progress section
cursor.execute("SELECT COUNT(*) FROM questions")
total_questions = cursor.fetchone()[0]

cursor.execute('SELECT COUNT(*) FROM student_answers WHERE student_id = ?', (st.session_state.user_id,))
answered_questions = cursor.fetchone()[0]

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### 📈 Progress Tes")

if total_questions > 0:
    progress = answered_questions / total_questions
    st.progress(progress)
    st.markdown(f"""
    <p style="color: #475569; text-align: center;">
        Soal dijawab: <span style="color: #1e3a8a; font-weight: 600;">{answered_questions}</span> 
        dari <span style="color: #0f172a; font-weight: 600;">{total_questions}</span> soal 
        ({progress*100:.1f}%)
    </p>
    """, unsafe_allow_html=True)
else:
    st.warning("Belum ada soal yang tersedia. Hubungi administrator.")

# Info section
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("#### ℹ️ Informasi")

with st.expander("Tentang Tes Minat Bakat Holland"):
    st.markdown("""
    **Tes Minat Bakat Holland** membantu Anda memahami:
    
    | Aspek | Deskripsi |
    |-------|-----------|
    | **Tipe Kepribadian** | Berdasarkan 6 tipe Holland (RIASEC) |
    | **Minat Karier** | Bidang pekerjaan yang sesuai |
    | **Rekomendasi Jurusan** | Saran jurusan kuliah yang cocok |
    
    **6 Tipe Holland:**
    - 🔧 **Realistic** - Praktis, suka bekerja dengan tangan
    - 🔬 **Investigative** - Analitis, suka memecahkan masalah
    - 🎨 **Artistic** - Kreatif, suka berkarya seni
    - 👥 **Social** - Suka membantu orang lain
    - 💼 **Enterprising** - Suka memimpin dan berbisnis
    - 📊 **Conventional** - Terorganisir, suka data
    """)

with st.expander("Cara Mengerjakan Tes"):
    st.markdown("""
    1. **Baca setiap pernyataan** dengan teliti
    2. **Pilih jawaban** yang paling sesuai:
       - 1 = Sangat Tidak Setuju
       - 5 = Sangat Setuju
    3. **Jawab dengan jujur** sesuai perasaan Anda
    4. **Selesaikan semua soal** untuk hasil akurat
    """)

conn.close()