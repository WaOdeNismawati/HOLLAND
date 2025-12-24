import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
from database.db_manager import DatabaseManager
from utils.auth import check_login, logout
from utils.config import connection
from components.sidebar import render_sidebar
from utils.styles import apply_dark_theme, get_chart_color_scheme
import json

st.set_page_config(page_title="Dashboard Admin", page_icon="👨‍💼", layout="wide", initial_sidebar_state="expanded")

# Apply dark theme
apply_dark_theme()

@st.cache_data(ttl=30)
def get_dashboard_stats():
    """Cache dashboard statistics for 30 seconds"""
    conn = connection()
    cursor = conn.cursor()
    
    # Total siswa
    cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
    total_students = cursor.fetchone()[0]
    
    # Siswa yang sudah mengerjakan tes
    cursor.execute("SELECT COUNT(*) FROM test_results")
    completed_tests = cursor.fetchone()[0]
    
    # Total soal
    cursor.execute("SELECT COUNT(*) FROM questions")
    total_questions = cursor.fetchone()[0]
    
    conn.close()
    
    return {
        'total_students': total_students,
        'completed_tests': completed_tests,
        'not_completed': total_students - completed_tests,
        'total_questions': total_questions
    }

@st.cache_data(ttl=30)
def get_recent_students():
    """Cache recent students data for 30 seconds"""
    conn = connection()
    cursor = conn.cursor()
    
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
    conn.close()
    
    return students_data

@st.cache_data(ttl=60)
def get_holland_distribution():
    """Cache Holland distribution data for 60 seconds"""
    conn = connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM test_results')
    completed_tests = cursor.fetchone()[0]
    
    if completed_tests == 0:
        conn.close()
        return None
    
    cursor.execute('SELECT holland_scores FROM test_results')
    holland_data = cursor.fetchall()
    conn.close()
    
    # Aggregate Holland scores
    holland_totals = {
        'Realistic': 0, 'Investigative': 0, 'Artistic': 0,
        'Social': 0, 'Enterprising': 0, 'Conventional': 0
    }
    
    for row in holland_data:
        scores = json.loads(row[0])
        for holland_type, score in scores.items():
            holland_totals[holland_type] += score
    
    return holland_totals

# Cek login
check_login()

# Render sidebar
st.session_state.current_page = 'admin_dashboard'
render_sidebar()

if st.session_state.role != 'admin':
    st.error("Akses ditolak! Halaman ini hanya untuk admin.")
    st.stop()

# Get cached statistics
stats = get_dashboard_stats()

# Statistik utama
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Siswa", stats['total_students'])

with col2:
    st.metric("Tes Selesai", stats['completed_tests'])

with col3:
    st.metric("Belum Mengerjakan", stats['not_completed'])

with col4:
    st.metric("Total Soal", stats['total_questions'])

st.markdown("---")

# Grafik status pengerjaan tes
st.subheader("📈 Status Pengerjaan Tes")

col1, col2 = st.columns([2, 1])

with col1:
    # Data untuk grafik
    status_data = {
        'Status': ['Sudah Mengerjakan', 'Belum Mengerjakan'],
        'Jumlah': [stats['completed_tests'], stats['not_completed']]
    }
    
    df_status = pd.DataFrame(status_data)
    
    # Grafik bar
    fig = px.bar(df_status, x='Status', y='Jumlah', 
                 color='Status',
                 color_discrete_map={
                     'Sudah Mengerjakan': '#2E8B57',
                     'Belum Mengerjakan': '#DC143C'
                 },
                 title="Distribusi Status Pengerjaan Tes",
                 template='plotly_dark')
    
    fig.update_layout(
        showlegend=False,
        paper_bgcolor='rgba(26, 26, 46, 0.5)',
        plot_bgcolor='rgba(22, 33, 62, 0.3)'
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Pie chart
    if stats['total_students'] > 0:
        fig_pie = px.pie(df_status, values='Jumlah', names='Status',
                        color_discrete_map={
                            'Sudah Mengerjakan': '#2E8B57',
                            'Belum Mengerjakan': '#DC143C'
                        },
                        title="Persentase Status",
                        template='plotly_dark')
        fig_pie.update_layout(
            paper_bgcolor='rgba(26, 26, 46, 0.5)',
            plot_bgcolor='rgba(22, 33, 62, 0.3)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)

# Tabel siswa terbaru
st.subheader("👥 Siswa Terbaru")
students_data = get_recent_students()

if students_data:
    df_students = pd.DataFrame(students_data, 
                              columns=['Nama Lengkap', 'Kelas', 'Tanggal Daftar', 'Status Tes'])
    st.dataframe(df_students, use_container_width=True)
else:
    st.info("Belum ada data siswa.")

# Distribusi tipe Holland (jika ada hasil tes)
holland_totals = get_holland_distribution()

if holland_totals:
    st.subheader("🎯 Distribusi Tipe Holland")
    
    df_holland = pd.DataFrame(list(holland_totals.items()), 
                             columns=['Tipe Holland', 'Total Skor'])
    
    fig_holland = px.bar(df_holland, x='Tipe Holland', y='Total Skor',
                        color='Tipe Holland',
                        title="Distribusi Total Skor Tipe Holland",
                        template='plotly_dark')
    fig_holland.update_layout(
        paper_bgcolor='rgba(26, 26, 46, 0.5)',
        plot_bgcolor='rgba(22, 33, 62, 0.3)'
    )
    st.plotly_chart(fig_holland, use_container_width=True)