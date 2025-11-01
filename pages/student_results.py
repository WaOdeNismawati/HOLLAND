import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from database.db_manager import DatabaseManager
from utils.auth import check_login
from utils.navbar import show_navbar

# Cek login dan tampilkan navbar
check_login()
show_navbar()

if st.session_state.role != 'student':
    st.error("Akses ditolak! Halaman ini hanya untuk siswa.")
    st.stop()

st.set_page_config(page_title="Hasil Tes", page_icon="📊", layout="wide")

# Main content
st.title("📊 Hasil Tes Minat Bakat Anda")
st.markdown("---")

# Database connection
db_manager = DatabaseManager()
conn = db_manager.get_connection()
cursor = conn.cursor()

# Ambil hasil tes siswa
cursor.execute('''
    SELECT holland_scores, anp_results, top_3_types, recommended_major, completed_at
    FROM test_results 
    WHERE student_id = ?
''', (st.session_state.user_id,))

result = cursor.fetchone()
conn.close()

if not result:
    st.warning("⚠️ Anda belum menyelesaikan tes minat bakat.")
    if st.button("Mulai Tes Sekarang", type="primary"):
        st.switch_page("pages/student_test.py")
    st.stop()

# Parse data
holland_scores = json.loads(result[0])
anp_results = json.loads(result[1]) if result[1] else {}
top_3_types = json.loads(result[2])
recommended_major = result[3]
completed_at = result[4]

st.success(f"Tes diselesaikan pada: **{completed_at}**")

# --- Tampilan Hasil ---
st.subheader("🎯 Rekomendasi Jurusan Terbaik")
st.success(f"**🏆 {recommended_major}**")

st.markdown("---")

col1, col2 = st.columns(2)

with col1:
    st.subheader("🏅 Peringkat Rekomendasi Jurusan")
    ranked_majors = anp_results.get('ranked_majors', [])
    if ranked_majors:
        majors_df = [{"Peringkat": i + 1, "Jurusan": major, "Prioritas": f"{score:.4f}"}
                       for i, (major, score) in enumerate(ranked_majors[:5])]
        st.dataframe(majors_df, use_container_width=True, hide_index=True)
    else:
        st.info("Tidak ada data peringkat.")

with col2:
    st.subheader("📊 Tipe Kepribadian Teratas")
    if top_3_types:
        for tipe in top_3_types:
            st.metric(label=tipe, value=holland_scores.get(tipe, 0))

st.markdown("---")

st.subheader("📈 Profil Skor Holland Anda")

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
    height=400
)
st.plotly_chart(fig_radar, use_container_width=True)

# Interpretasi hasil
st.markdown("---")
st.subheader("💡 Interpretasi Hasil")

holland_descriptions = {
    'Realistic': 'Praktis, suka bekerja dengan tangan dan alat',
    'Investigative': 'Analitis, suka memecahkan masalah kompleks',
    'Artistic': 'Kreatif, suka berkarya seni dan berekspresi',
    'Social': 'Suka membantu dan berinteraksi dengan orang',
    'Enterprising': 'Suka memimpin, berbisnis, dan mengambil risiko',
    'Conventional': 'Terorganisir, suka bekerja dengan data dan sistem'
}

with st.expander("Penjelasan Tipe Kepribadian Anda", expanded=True):
    for holland_type in top_3_types:
        st.write(f"**{holland_type}:** {holland_descriptions.get(holland_type, '')}")

with st.expander("Saran Pengembangan Karier"):
    st.write(f"""
    Berdasarkan analisis ANP dan profil RIASEC Anda, berikut adalah saran karier:
    
    **🏆 Jurusan Utama yang Direkomendasikan:** {recommended_major}
    
    **📚 5 Pilihan Terbaik:** {', '.join([major[0] for major in ranked_majors[:5]])}
    
    **🚀 Tips Pengembangan:**
    - Fokus mengembangkan keterampilan **{top_3_types[0]}** sebagai kekuatan utama.
    - Perkuat kemampuan **{top_3_types[1]}** dan **{top_3_types[2]}** sebagai pendukung.
    - Cari pengalaman magang atau proyek di bidang terkait 5 jurusan teratas.
    """)