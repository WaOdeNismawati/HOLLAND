import streamlit as st
from utils.auth import check_login
from utils.holland_calculator import HollandCalculator
from utils.config import connection

# Cek login & koneksi database
check_login()
conn = connection()

if st.session_state.role != 'student':
    st.error("Akses ditolak! Halaman ini hanya untuk siswa.")
    st.stop()

st.set_page_config(page_title="Tes Minat Bakat", page_icon="📝", layout="wide")


# Main content
st.title("📝 Tes Minat Bakat Holland")
st.markdown("---")

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
        with st.spinner("📄 Memproses hasil tes..."):
            calculator = HollandCalculator()
            result = calculator.process_test_completion(st.session_state.user_id)
        
        st.success("🎉 Tes berhasil diselesaikan!")
        st.balloons()
        
        # Tampilkan hasil singkat
        st.subheader("📊 Hasil Tes Anda:")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Holland Code:**")
            st.info(f"**{result['holland_code']}**")
            
            st.write("**3 Tipe Kepribadian Teratas:**")
            for i, holland_type in enumerate(result['top_3_types'], 1):
                score = result['scores'][holland_type]
                st.write(f"{i}. {holland_type} ({score:.3f})")
        
        with col2:
            st.write("**Rekomendasi Jurusan Terbaik:**")
            if result.get('recommended_major'):
                st.success(f"🎓 {result['recommended_major']}")
            else:
                st.warning("Rekomendasi tidak tersedia")
            
            # Show top recommendations from ANP
            if result.get('anp_results') and result['anp_results'].get('top_5_majors'):
                st.write("**Alternatif Pilihan Lainnya:**")
                top_5 = result['anp_results']['top_5_majors']
                
                # Show next 3 alternatives
                for i, major_data in enumerate(top_5[1:4], 2):
                    if isinstance(major_data, dict):
                        major_name = major_data.get('major_name', 'Unknown')
                        score = major_data.get('anp_score', 0)
                        st.write(f"{i}. {major_name} (Score: {score:.4f})")
                    elif isinstance(major_data, (list, tuple)) and len(major_data) >= 2:
                        major_name = major_data[0]
                        data = major_data[1]
                        score = data.get('anp_score', 0)
                        st.write(f"{i}. {major_name} (Score: {score:.4f})")
            elif result.get('holland_filter') and result['holland_filter'].get('filtered_majors'):
                # Fallback to Holland filter results
                st.write("**Alternatif Pilihan Lainnya (Holland Similarity):**")
                filtered = result['holland_filter']['filtered_majors']
                similarity_scores = result['holland_filter'].get('similarity_scores', {})
                
                for i, major in enumerate(filtered[1:4], 2):
                    sim_score = similarity_scores.get(major, 0)
                    st.write(f"{i}. {major} (Similarity: {sim_score:.3f})")
        
        # Info metodologi
        with st.expander("ℹ️ Bagaimana hasil ini dihitung?"):
            st.write("""
            **Metode yang digunakan:**
            1. **Holland Code (RIASEC)**: Mengidentifikasi tipe kepribadian Anda berdasarkan 6 dimensi
            2. **Similarity Filtering**: Menyaring jurusan yang sesuai dengan profil Holland Anda menggunakan cosine similarity
            3. **ANP (Analytic Network Process)**: Meranking jurusan hasil filter untuk rekomendasi terbaik menggunakan analisis jaringan
            
            **Keunggulan metode ini:**
            - **Akurat**: Menggabungkan teori Holland yang teruji dengan analisis multi-kriteria ANP
            - **Efisien**: Filter Holland mengurangi kompleksitas sebelum analisis ANP
            - **Komprehensif**: Mempertimbangkan ketergantungan dan feedback antar dimensi kepribadian
            - **Valid**: Menggunakan consistency ratio untuk memastikan kekonsistenan penilaian
            """)
            
            # Show ANP calculation details if available
            if result.get('anp_results') and result['anp_results'].get('calculation_details'):
                calc_details = result['anp_results']['calculation_details']
                
                st.write("**Detail Perhitungan ANP:**")
                st.write(f"- Consistency Ratio: {calc_details.get('consistency_ratio', 0):.4f}")
                st.write(f"- Status: {'Konsisten ✓' if calc_details.get('is_consistent', False) else 'Perlu review'}")
                st.write(f"- Iterasi konvergen: {calc_details.get('iterations', 0)}")
                st.write(f"- Dimensi supermatrix: {calc_details.get('supermatrix_size', 0)}")
        
        # Info Holland Filter
        if result.get('holland_filter'):
            holland_filter = result['holland_filter']
            with st.expander("🔍 Detail Holland Filtering"):
                st.write(f"**Total jurusan yang dianalisis:** {holland_filter.get('total_filtered', 0)}")
                st.write(f"**Jurusan yang lolos filter:** {len(holland_filter.get('filtered_majors', []))}")
                
                if holland_filter.get('similarity_scores'):
                    st.write("**Top 5 Similarity Scores:**")
                    sim_scores = holland_filter['similarity_scores']
                    sorted_sim = sorted(sim_scores.items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    for i, (major, score) in enumerate(sorted_sim, 1):
                        st.write(f"{i}. {major}: {score:.3f}")
        
        # Tombol untuk melihat hasil lengkap
        st.markdown("---")
        if st.button("📄 Lihat Hasil Lengkap & Detail Analisis ANP", type="primary", use_container_width=True):
            st.switch_page("pages/student_results.py")
            
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {str(e)}")
        with st.expander("🔍 Detail Error (untuk debugging)"):
            import traceback
            st.code(traceback.format_exc())
        conn.rollback()

conn.close()