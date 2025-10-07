import streamlit as st
import pandas as pd
import json
import plotly.graph_objects as go
from database.db_manager import DatabaseManager
from utils.auth import check_login

# Cek login
check_login()

if st.session_state.role != 'admin':
    st.error("Akses ditolak! Halaman ini hanya untuk admin.")
    st.stop()

st.set_page_config(page_title="Monitoring Hasil Tes", page_icon="📊", layout="wide")

# Sidebar
with st.sidebar:
    st.title("📊 Monitoring Tes")
    st.write(f"Admin: {st.session_state.full_name}")
    
    if st.button("🏠 Dashboard Admin"):
        st.switch_page("pages/admin_dashboard.py")

# Main content
st.title("📊 Monitoring Hasil Tes")
st.markdown("---")

# Database connection
db_manager = DatabaseManager()
conn = db_manager.get_connection()
cursor = conn.cursor()

# --- Section for Aggregate Statistics ---
st.subheader("📈 Statistik Umum")

# Fetch all test results for statistics
cursor.execute("SELECT anp_results FROM test_results")
all_results_data = cursor.fetchall()

total_tests = len(all_results_data)
majors = []
dominant_types = []

for (anp_json,) in all_results_data:
    if anp_json:
        try:
            anp_data = json.loads(anp_json)
            if anp_data.get('ranked_majors') and anp_data['ranked_majors']:
                majors.append(anp_data['ranked_majors'][0][0])  # Top major
            if anp_data.get('top_3_criteria'):
                dominant_types.append(list(anp_data['top_3_criteria'].keys())[0])
        except (json.JSONDecodeError, IndexError):
            continue

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Total Hasil Tes", total_tests)
with col2:
    most_popular_major = max(set(majors), key=majors.count) if majors else "N/A"
    st.metric("Jurusan Terpopuler", most_popular_major)
with col3:
    most_dominant_type = max(set(dominant_types), key=dominant_types.count) if dominant_types else "N/A"
    st.metric("Tipe Dominan", most_dominant_type)

st.markdown("---")
# --- End of Statistics Section ---

st.subheader("Individual Student History")

# Ambil daftar siswa
cursor.execute("SELECT id, full_name, class_name FROM users WHERE role = 'student' ORDER BY full_name")
students = cursor.fetchall()

if not students:
    st.info("Belum ada data siswa terdaftar.")
    st.stop()

# Dropdown untuk memilih siswa
student_options = {f"{name} ({class_name or 'N/A'})": student_id for student_id, name, class_name in students}
selected_student_name = st.selectbox("Pilih Siswa untuk Melihat Riwayat Tes", options=list(student_options.keys()))

if selected_student_name:
    student_id = student_options[selected_student_name]

    # Ambil semua hasil tes untuk siswa yang dipilih
    cursor.execute('''
        SELECT id, holland_scores, anp_results, completed_at
        FROM test_results
        WHERE student_id = ?
        ORDER BY completed_at DESC
    ''', (student_id,))
    
    results = cursor.fetchall()
    
    st.subheader(f"Riwayat Tes untuk: {selected_student_name}")

    if not results:
        st.warning("Siswa ini belum pernah menyelesaikan tes.")
    else:
        st.info(f"Ditemukan **{len(results)}** riwayat tes untuk siswa ini.")
        
        # Tampilkan setiap hasil tes dalam expander
        for i, result in enumerate(results):
            result_id, holland_scores_json, anp_results_json, completed_at = result
            
            holland_scores = json.loads(holland_scores_json)
            anp_results = json.loads(anp_results_json) if anp_results_json else {}

            header = f"📜 Hasil Tes #{len(results) - i} - Diselesaikan pada: {completed_at}"

            with st.expander(header, expanded=(i == 0)):
                top_3_criteria = anp_results.get('top_3_criteria', {})
                ranked_majors = anp_results.get('ranked_majors', [])
                
                if not top_3_criteria or not ranked_majors:
                    st.warning("Data hasil ANP tidak lengkap untuk tes ini.")
                    continue

                st.subheader("🎯 Rekomendasi Jurusan Utama")
                top_major, top_score = ranked_majors[0]
                st.success(f"**🏆 {top_major}** (Prioritas ANP: {top_score:.4f})")

                st.markdown("---")

                col1, col2 = st.columns([1, 2])

                with col1:
                    st.subheader("📊 Tipe Kepribadian Teratas")
                    for tipe, score in top_3_criteria.items():
                        st.metric(label=tipe, value=int(score))

                with col2:
                    st.subheader("🏅 Peringkat Rekomendasi Jurusan")
                    if len(ranked_majors) > 1:
                        other_majors_df = [{"Peringkat": i + 1, "Jurusan": major, "Prioritas": f"{score:.4f}"}
                                           for i, (major, score) in enumerate(ranked_majors[:5])]
                        st.dataframe(other_majors_df, use_container_width=True, hide_index=True)

                st.markdown("---")

                st.subheader("📈 Profil Skor Holland")

                # Radar chart
                categories = list(holland_scores.keys())
                values = list(holland_scores.values())

                fig_radar = go.Figure()
                fig_radar.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name='Skor'
                ))

                fig_radar.update_layout(
                    polar=dict(radialaxis=dict(visible=True, range=[0, max(values) + 5 if values else 25])),
                    title="Visualisasi Skor Holland",
                    height=350
                )
                st.plotly_chart(fig_radar, use_container_width=True)

conn.close()