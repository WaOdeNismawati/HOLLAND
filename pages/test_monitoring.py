import streamlit as st
import pandas as pd
import json
import plotly.express as px
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
st.title("📊 Monitoring Hasil Tes Siswa")
st.markdown("---")

# Database connection
db_manager = DatabaseManager()
conn = db_manager.get_connection()
cursor = conn.cursor()

# Ambil data hasil tes
cursor.execute('''
    SELECT u.full_name, u.class_name, tr.top_3_types, tr.recommended_major,
           tr.holland_scores, tr.completed_at
    FROM test_results tr
    JOIN users u ON tr.student_id = u.id
    ORDER BY tr.completed_at DESC
''')

results_data = cursor.fetchall()
conn.close()

if not results_data:
    st.info("Belum ada siswa yang menyelesaikan tes.")
    st.stop()

# --- Statistik Umum ---
st.subheader("📈 Statistik Umum")
majors = [row[3] for row in results_data]
all_top_types = [json.loads(row[2])[0] for row in results_data if row[2] and len(json.loads(row[2])) > 0]

with col1:
    st.metric("Total Hasil Tes", len(results_data))
with col2:
    # Jurusan paling populer
    majors = [row[3] for row in results_data]
    most_popular_major = max(set(majors), key=majors.count) if majors else "N/A"
    st.metric("Jurusan Terpopuler", most_popular_major)

with col3:
    most_dominant_type = max(set(all_top_types), key=all_top_types.count) if all_top_types else "N/A"
    st.metric("Tipe Dominan", most_dominant_type)

with col4:
    # Rata-rata hari ini
    from datetime import datetime, date
    today_results = [row for row in results_data if row[5].startswith(str(date.today()))]
    st.metric("Tes Hari Ini", len(today_results))

st.markdown("---")

# --- Filter dan Pencarian ---
st.subheader("🔍 Filter dan Pencarian")
col1, col2, col3 = st.columns(3)
with col1:
    all_classes = sorted(list(set([row[1] for row in results_data if row[1]])))
    selected_class = st.selectbox("Filter Kelas", options=['Semua'] + all_classes)
with col2:
    all_majors = sorted(list(set([row[3] for row in results_data])))
    selected_major = st.selectbox("Filter Jurusan", options=['Semua'] + all_majors)
with col3:
    search_name = st.text_input("Cari Nama Siswa")

# Apply filters
filtered_data = [
    row for row in results_data
    if (selected_class == 'Semua' or row[1] == selected_class) and
       (selected_major == 'Semua' or row[3] == selected_major) and
       (search_name.lower() in row[0].lower())
]

# --- Tabel Hasil ---
st.subheader("📋 Hasil Tes Siswa")
if filtered_data:
    display_data = [{
        'Nama': row[0], 'Kelas': row[1] or 'N/A',
        'Tipe 1': json.loads(row[2])[0], 'Tipe 2': json.loads(row[2])[1], 'Tipe 3': json.loads(row[2])[2],
        'Jurusan Rekomendasi': row[3], 'Tanggal Tes': row[4]
    } for row in filtered_data]
    
    df_results = pd.DataFrame(display_data)
    st.dataframe(df_results, use_container_width=True, hide_index=True)
else:
    st.info("Tidak ada data yang sesuai dengan filter.")
