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

# Block test if already completed
cursor.execute('SELECT COUNT(*) FROM test_results WHERE student_id = ?', (st.session_state.user_id,))
if cursor.fetchone()[0] > 0:
    st.warning("⚠️ Anda sudah menyelesaikan tes ini.")
    st.info("Jika Anda ingin mengambil tes kembali, silakan hubungi administrator untuk mereset hasil Anda.")
    if st.button("Lihat Hasil Tes"):
        st.switch_page("pages/student_results.py")
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
    with st.spinner("Menghitung hasil..."):
        try:
            calculator = HollandCalculator()
            result = calculator.process_test_completion(st.session_state.user_id, answers)
            
            # Show top 3 ANP recommendations if available
            if 'anp_results' in result and result['anp_results']:
                st.write("**Top 3 Pilihan Lainnya:**")
                top_majors = result['anp_results']['top_5_majors'][:3]
                for i, (major, data) in enumerate(top_majors[1:], 2):  # Skip first as it's already shown
                    st.write(f"{i}. {major} ({data['final_score']:.2f})")
                    if i >= 3:  # Only show top 3 additional
                        break
        
        # Tombol untuk melihat hasil lengkap
        if st.button("Lihat Hasil Lengkap", type="primary"):
            st.switch_page("pages/student_results.py")
            
            st.subheader("📊 Hasil Rekomendasi Jurusan (Metode ANP)")

            anp_results = result.get('anp_results', {})
            top_3_criteria = anp_results.get('top_3_types', [])
            ranked_majors = anp_results.get('ranked_majors', [])

            if top_3_criteria:
                st.write("**Tiga Tipe Kepribadian Teratas Anda:**")
                cols = st.columns(len(top_3_criteria))
                for idx, tipe in enumerate(top_3_criteria):
                    cols[idx].metric(label=tipe, value=result['scores'][tipe])

            if ranked_majors:
                st.write("**Peringkat Rekomendasi Jurusan:**")
                top_major, top_score = ranked_majors[0]
                st.success(f"**🏆 Rekomendasi Utama: {top_major}** (Prioritas: {top_score:.4f})")

                if len(ranked_majors) > 1:
                    st.write("Pilihan lainnya:")
                    other_majors_df = [{"Peringkat": i + 2, "Jurusan": major, "Prioritas": f"{score:.4f}"}
                                       for i, (major, score) in enumerate(ranked_majors[1:5])]
                    st.table(other_majors_df)
            else:
                st.warning("Tidak dapat menghasilkan rekomendasi.")

            st.markdown("---")
            if st.button("Lihat Detail Hasil", type="primary"):
                st.switch_page("pages/student_results.py")

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses hasil: {str(e)}")

conn.close()