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

# Cek apakah siswa pernah mengerjakan tes sebelumnya untuk memberikan opsi retake
cursor.execute('SELECT COUNT(*) FROM test_results WHERE student_id = ?', (st.session_state.user_id,))
has_previous_results = cursor.fetchone()[0] > 0

if has_previous_results:
    st.info("Anda telah menyelesaikan tes ini sebelumnya. Anda dapat mengambilnya kembali untuk mendapatkan rekomendasi terbaru.")

# Ambil semua soal
cursor.execute('SELECT id, question_text FROM questions ORDER BY id')
questions = cursor.fetchall()

if not questions:
    st.error("Tidak ada soal yang tersedia. Hubungi administrator.")
    st.stop()

st.info(f"📋 Jawab {len(questions)} pernyataan berikut dengan skala 1 (Sangat Tidak Setuju) sampai 5 (Sangat Setuju).")

with st.form("test_form"):
    answers = {}
    for i, (question_id, question_text) in enumerate(questions, 1):
        st.write(f"**{i}. {question_text}**")
        answer = st.radio(
            f"Pilih jawaban untuk soal {i}:",
            options=[1, 2, 3, 4, 5],
            index=2, # Default to neutral
            key=f"q_{question_id}",
            horizontal=True,
            label_visibility="collapsed"
        )
        answers[question_id] = answer
        
    
    st.markdown("---")
    submit_button = st.form_submit_button("🚀 Selesaikan & Lihat Hasil", type="primary", use_container_width=True)

if submit_button:
    with st.spinner("Menghitung hasil..."):
        try:
            # The new process_test_completion handles all database operations.
            # We just need to pass the student_id and the collected answers.
            calculator = HollandCalculator()
            result = calculator.process_test_completion(st.session_state.user_id, answers)
            print("user_id")
            print(result)
            
            st.success("🎉 Tes berhasil diselesaikan! Berikut adalah hasilnya.")
            st.balloons()
            
            st.subheader("📊 Hasil Rekomendasi Jurusan (Metode ANP)")

            anp_results = result.get('anp_results', {})
            top_3_criteria = anp_results.get('top_3_criteria', {})
            ranked_majors = anp_results.get('ranked_majors', [])

            if top_3_criteria:
                st.write("**Tiga Tipe Kepribadian Teratas Anda:**")
                cols = st.columns(len(top_3_criteria))
                for idx, (tipe, score) in enumerate(top_3_criteria.items()):
                    cols[idx].metric(label=tipe, value=int(score))

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
                st.warning("Tidak dapat menghasilkan rekomendasi. Pastikan data jurusan (alternatives) tersedia.")

            st.markdown("---")
            if st.button("Lihat Semua Riwayat Tes", type="primary"):
                st.switch_page("pages/student_results.py")

        except Exception as e:
            st.error(f"Terjadi kesalahan saat memproses hasil: {str(e)}")
            conn.rollback()

conn.close()