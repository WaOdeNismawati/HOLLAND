import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from database.db_manager import DatabaseManager
from utils.auth import check_login

# Cek login
check_login()

if st.session_state.role != 'student':
    st.error("Akses ditolak! Halaman ini hanya untuk siswa.")
    st.stop()

st.set_page_config(page_title="Hasil Tes", page_icon="📊", layout="wide")

# Sidebar
with st.sidebar:
    st.title("📊 Hasil Tes")
    st.write(f"Siswa: {st.session_state.full_name}")
    
    if st.button("🏠 Kembali ke Dashboard"):
        st.switch_page("pages/student_dashboard.py")

# Main content
st.title("📊 Hasil Tes Minat Bakat")
st.markdown("---")

# Database connection
db_manager = DatabaseManager()
conn = db_manager.get_connection()
cursor = conn.cursor()

# Ambil semua hasil tes siswa, diurutkan dari yang terbaru
cursor.execute('''
    SELECT id, holland_scores, anp_results, completed_at
    FROM test_results 
    WHERE student_id = ?
    ORDER BY completed_at DESC
''', (st.session_state.user_id,))

results = cursor.fetchall()
conn.close()

if not results:
    st.warning("⚠️ Anda belum pernah menyelesaikan tes minat bakat.")
    if st.button("Mulai Tes Sekarang", type="primary"):
        st.switch_page("pages/student_test.py")
    st.stop()

st.info(f"Anda telah menyelesaikan tes sebanyak **{len(results)}** kali. Berikut adalah riwayat hasil tes Anda.")

# Tampilkan setiap hasil tes dalam expander
for i, result in enumerate(results):
    _, holland_scores_json, anp_results_json, completed_at = result
    
    holland_scores = json.loads(holland_scores_json)
    anp_results = json.loads(anp_results_json) if anp_results_json else {}
    
    header = f"📜 Hasil Tes #{len(results) - i} - Diselesaikan pada: {completed_at}"

    with st.expander(header, expanded=(i == 0)): # Buka expander pertama secara default
        
        top_3_criteria = anp_results.get('top_3_criteria', {})
        ranked_majors = anp_results.get('ranked_majors', [])
        
        if not top_3_criteria or not ranked_majors:
            st.warning("Data hasil tidak lengkap untuk tes ini.")
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
                st.dataframe(other_majors_df, use_container_width=True)
        
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
            name='Skor Anda'
        ))
        
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, max(values) + 5 if values else 25])),
            title="Visualisasi Skor Holland",
            height=350
        )
        st.plotly_chart(fig_radar, use_container_width=True)

# Tombol untuk kembali ke dashboard atau mengambil tes lagi
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Ambil Tes Lagi", use_container_width=True):
        st.switch_page("pages/student_test.py")
with col2:
    if st.button("🏠 Kembali ke Dashboard", use_container_width=True):
        st.switch_page("pages/student_dashboard.py")