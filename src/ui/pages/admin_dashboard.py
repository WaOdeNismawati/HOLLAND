import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px

from src.core.auth import check_login, logout
from src.core.config import connection
from src.ui.components.navbar_components import show_top_navbar
from src.ui.components.sidebar import sidebar

# # Cek login
# check_login()
# # Database connection
# db_manager = DatabaseManager()
# conn = db_manager.get_connection()
conn = connection()

if st.session_state.role != 'admin':
    st.error("Akses ditolak! Halaman ini hanya untuk admin.")
    st.stop()

st.set_page_config(page_title="Dashboard Admin", page_icon="👨‍💼", layout="wide")

# Sidebar
sidebar()

# Main content
st.title("📊 Dashboard Admin")
st.markdown("---")

# Statistik utama
col1, col2, col3, col4 = st.columns(4)

# Total siswa
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
total_students = cursor.fetchone()[0]

# Siswa yang sudah mengerjakan tes
cursor.execute("SELECT COUNT(*) FROM test_results")
completed_tests = cursor.fetchone()[0]

# Siswa yang belum mengerjakan tes
not_completed = total_students - completed_tests

# Total soal
cursor.execute("SELECT COUNT(*) FROM questions")
total_questions = cursor.fetchone()[0]

with col1:
    st.metric("Total Siswa", total_students)

with col2:
    st.metric("Tes Selesai", completed_tests)

with col3:
    st.metric("Belum Mengerjakan", not_completed)

with col4:
    st.metric("Total Soal", total_questions)

st.markdown("---")

# Grafik status pengerjaan tes
st.subheader("📈 Status Pengerjaan Tes")

col1, col2 = st.columns([2, 1])

with col1:
    # Data untuk grafik
    status_data = {
        'Status': ['Sudah Mengerjakan', 'Belum Mengerjakan'],
        'Jumlah': [completed_tests, not_completed]
    }
    
    df_status = pd.DataFrame(status_data)
    
    # Grafik bar
    fig = px.bar(df_status, x='Status', y='Jumlah', 
                 color='Status',
                 color_discrete_map={
                     'Sudah Mengerjakan': '#2E8B57',
                     'Belum Mengerjakan': '#DC143C'
                 },
                 title="Distribusi Status Pengerjaan Tes")
    
    fig.update_layout(showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Pie chart
    if total_students > 0:
        fig_pie = px.pie(df_status, values='Jumlah', names='Status',
                        color_discrete_map={
                            'Sudah Mengerjakan': '#2E8B57',
                            'Belum Mengerjakan': '#DC143C'
                        },
                        title="Persentase Status")
        st.plotly_chart(fig_pie, use_container_width=True)

# Tabel siswa terbaru
st.subheader("👥 Siswa Terbaru")
cursor.execute('''
    SELECT u.full_name, u.class_name, u.created_at,
           CASE WHEN tr.id IS NOT NULL THEN 'Sudah' ELSE 'Belum' END as status_tes
    FROM users u
    LEFT JOIN test_results tr ON u.id = tr.student_id
    WHERE u.role = 'student'
    ORDER BY u.created_at DESC
    LIMIT 10
''')

students_data = cursor.fetchall()
if students_data:
    df_students = pd.DataFrame(students_data, 
                              columns=['Nama Lengkap', 'Kelas', 'Tanggal Daftar', 'Status Tes'])
    st.dataframe(df_students, use_container_width=True)
else:
    st.info("Belum ada data siswa.")

# Distribusi tipe Holland (jika ada hasil tes)
if completed_tests > 0:
    st.subheader("🎯 Distribusi Tipe Holland")
    
    cursor.execute('''
        SELECT holland_scores FROM test_results
    ''')
    
    holland_data = cursor.fetchall()
    
    # Aggregate Holland scores
    holland_totals = {
        'Realistic': 0, 'Investigative': 0, 'Artistic': 0,
        'Social': 0, 'Enterprising': 0, 'Conventional': 0
    }
    
    import json
    for row in holland_data:
        scores = json.loads(row[0])
        for holland_type, score in scores.items():
            holland_totals[holland_type] += score
    
    df_holland = pd.DataFrame(list(holland_totals.items()), 
                             columns=['Tipe Holland', 'Total Skor'])
    
    fig_holland = px.bar(df_holland, x='Tipe Holland', y='Total Skor',
                        color='Tipe Holland',
                        title="Distribusi Total Skor Tipe Holland")
    st.plotly_chart(fig_holland, use_container_width=True)

conn.close()