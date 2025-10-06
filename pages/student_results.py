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

# Ambil hasil tes siswa
cursor.execute('''
    SELECT top_3_types, recommended_major, holland_scores, completed_at
    FROM test_results 
    WHERE student_id = ?
''', (st.session_state.user_id,))

result = cursor.fetchone()

if not result:
    st.warning("⚠️ Anda belum menyelesaikan tes minat bakat.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Mulai Tes Sekarang", type="primary"):
            st.switch_page("pages/student_test.py")
    with col2:
        if st.button("Kembali ke Dashboard"):
            st.switch_page("pages/student_dashboard.py")
    st.stop()

# Parse hasil
top_3_types = json.loads(result[0])
recommended_major = result[1]
holland_scores = json.loads(result[2])
completed_at = result[3]

# Header hasil
st.success(f"✅ Tes diselesaikan pada: {completed_at}")

# Rekomendasi utama
st.subheader("🎯 Rekomendasi Jurusan")
st.markdown(f"""
<div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
    <h2 style="color: #155724; margin: 0;">🎓 {recommended_major}</h2>
    <p style="color: #155724; margin: 5px 0 0 0;">Jurusan yang direkomendasikan berdasarkan hasil tes Anda</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# 3 Tipe kepribadian teratas
st.subheader("🏆 3 Tipe Kepribadian Teratas")

col1, col2, col3 = st.columns(3)

holland_descriptions = {
    'Realistic': {
        'icon': '🔧',
        'title': 'Realistic',
        'desc': 'Praktis, suka bekerja dengan tangan dan alat'
    },
    'Investigative': {
        'icon': '🔬', 
        'title': 'Investigative',
        'desc': 'Analitis, suka memecahkan masalah kompleks'
    },
    'Artistic': {
        'icon': '🎨',
        'title': 'Artistic', 
        'desc': 'Kreatif, suka berkarya seni dan berekspresi'
    },
    'Social': {
        'icon': '👥',
        'title': 'Social',
        'desc': 'Suka membantu dan berinteraksi dengan orang'
    },
    'Enterprising': {
        'icon': '💼',
        'title': 'Enterprising',
        'desc': 'Suka memimpin, berbisnis, dan mengambil risiko'
    },
    'Conventional': {
        'icon': '📊',
        'title': 'Conventional',
        'desc': 'Terorganisir, suka bekerja dengan data dan sistem'
    }
}

columns = [col1, col2, col3]
for i, holland_type in enumerate(top_3_types):
    with columns[i]:
        desc = holland_descriptions[holland_type]
        score = holland_scores[holland_type]
        
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; border: 2px solid #dee2e6;">
            <div style="font-size: 2em;">{desc['icon']}</div>
            <h4 style="margin: 10px 0 5px 0; color: #495057;">#{i+1} {desc['title']}</h4>
            <p style="font-size: 0.9em; color: #6c757d; margin: 5px 0;">{desc['desc']}</p>
            <div style="background-color: #007bff; color: white; padding: 5px; border-radius: 5px; margin-top: 10px;">
                <strong>Skor: {score}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# Grafik skor Holland
st.subheader("📈 Skor Lengkap Tipe Holland")

col1, col2 = st.columns([2, 1])

with col1:
    # Bar chart
    df_scores = pd.DataFrame(list(holland_scores.items()), columns=['Tipe Holland', 'Skor'])
    df_scores = df_scores.sort_values('Skor', ascending=True)
    
    fig_bar = px.bar(df_scores, x='Skor', y='Tipe Holland', orientation='h',
                     color='Skor', color_continuous_scale='viridis',
                     title="Skor Tipe Holland Anda")
    
    fig_bar.update_layout(showlegend=False, height=400)
    st.plotly_chart(fig_bar, use_container_width=True)

with col2:
    # Radar chart
    categories = list(holland_scores.keys())
    values = list(holland_scores.values())
    
    fig_radar = go.Figure()
    
    fig_radar.add_trace(go.Scatterpolar(
        r=values,
        theta=categories,
        fill='toself',
        name='Skor Anda',
        line_color='rgb(0, 123, 255)'
    ))
    
    fig_radar.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, max(values) + 5]
            )),
        showlegend=False,
        title="Profil Holland Anda",
        height=400
    )
    
    st.plotly_chart(fig_radar, use_container_width=True)

# Interpretasi hasil
st.markdown("---")
st.subheader("💡 Interpretasi Hasil")

with st.expander("Penjelasan Tipe Kepribadian Anda", expanded=True):
    primary_type = top_3_types[0]
    primary_desc = holland_descriptions[primary_type]
    
    st.write(f"""
    **Tipe Utama Anda: {primary_desc['icon']} {primary_desc['title']}**
    
    {primary_desc['desc']}
    
    **Kombinasi 3 Tipe Teratas Anda:**
    """)
    
    for i, holland_type in enumerate(top_3_types, 1):
        desc = holland_descriptions[holland_type]
        st.write(f"{i}. **{desc['icon']} {desc['title']}:** {desc['desc']}")

with st.expander("Saran Pengembangan Karier"):
    st.write(f"""
    Berdasarkan hasil tes Anda, berikut adalah beberapa saran:
    
    **🎓 Jurusan yang Direkomendasikan:** {recommended_major}
    
    **💼 Bidang Karier yang Cocok:**
    - Bidang yang melibatkan karakteristik {top_3_types[0].lower()}
    - Pekerjaan yang memadukan aspek {top_3_types[1].lower()} dan {top_3_types[2].lower()}
    
    **🚀 Tips Pengembangan:**
    - Kembangkan keterampilan yang sesuai dengan tipe kepribadian utama Anda
    - Cari pengalaman yang menggabungkan ketiga tipe teratas Anda
    - Pertimbangkan untuk mengambil kursus atau pelatihan di bidang yang relevan
    """)

# Tombol aksi
st.markdown("---")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("🔄 Ulangi Tes", use_container_width=True):
        # Hapus hasil lama
        cursor.execute('DELETE FROM test_results WHERE student_id = ?', (st.session_state.user_id,))
        cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (st.session_state.user_id,))
        conn.commit()
        st.switch_page("pages/student_test.py")

with col2:
    if st.button("📄 Cetak Hasil", use_container_width=True):
        st.info("Fitur cetak akan segera tersedia!")

with col3:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/student_dashboard.py")

conn.close()