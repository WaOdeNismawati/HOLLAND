import streamlit as st
import pandas as pd
import plotly.express as px
import json
from database.db_manager import DatabaseManager
from utils.auth import check_login, logout
from utils.config import connection
from utils.styles import apply_dark_theme, render_sidebar, page_header


# Page config
st.set_page_config(page_title="Dashboard Admin", page_icon="📊", layout="wide")

# Apply dark theme and sidebar
apply_dark_theme()

# Check access
check_login()
if st.session_state.role != 'admin':
    st.error("Akses ditolak! Halaman ini hanya untuk admin.")
    st.stop()

# Render sidebar
render_sidebar(current_page="admin_dashboard")

# Database connection
conn = connection()
cursor = conn.cursor()

# Page header
page_header("Dashboard Admin", f"Selamat datang, {st.session_state.full_name}")


# Stats queries
cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'student'")
total_students = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM test_results")
completed_tests = cursor.fetchone()[0]

not_completed = total_students - completed_tests

cursor.execute("SELECT COUNT(*) FROM questions")
total_questions = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM majors")
total_majors = cursor.fetchone()[0]

# Stats cards
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("👥 Total Siswa", total_students)
with col2:
    st.metric("✅ Tes Selesai", completed_tests)
with col3:
    st.metric("⏳ Belum Tes", not_completed)
with col4:
    st.metric("📝 Total Soal", total_questions)

st.markdown("<br>", unsafe_allow_html=True)

# Charts section
col_chart1, col_chart2 = st.columns([2, 1])

with col_chart1:
    st.markdown("#### 📈 Status Pengerjaan Tes")
    
    status_data = {
        'Status': ['Sudah Mengerjakan', 'Belum Mengerjakan'],
        'Jumlah': [completed_tests, not_completed]
    }
    df_status = pd.DataFrame(status_data)
    
    fig = px.bar(
        df_status, x='Status', y='Jumlah',
        color='Status',
        color_discrete_map={
            'Sudah Mengerjakan': '#10b981',
            'Belum Mengerjakan': '#6b7280'
        }
    )
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#f1f5f9', # Light text for Dark Navy background
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

with col_chart2:
    st.markdown("#### 📊 Persentase")
    if total_students > 0:
        fig_pie = px.pie(
            df_status, values='Jumlah', names='Status',
            color_discrete_sequence=['#10b981', '#6b7280'],
            hole=0.4
        )
        fig_pie.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#f1f5f9', # Light text
            margin=dict(l=0, r=0, t=20, b=0)
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info("Belum ada data siswa.")

# Recent students table
st.markdown("#### 👥 Siswa Terbaru")
cursor.execute('''
    SELECT u.full_name, u.class_name, u.created_at,
           CASE WHEN tr.id IS NOT NULL THEN 'Selesai' ELSE 'Belum' END as status_tes,
           tr.recommended_major
    FROM users u
    LEFT JOIN test_results tr ON u.id = tr.student_id
    WHERE u.role = 'student'
    ORDER BY u.created_at DESC
    LIMIT 10
''')

students_data = cursor.fetchall()
if students_data:
    df_students = pd.DataFrame(
        students_data,
        columns=['Nama', 'Kelas', 'Terdaftar', 'Status', 'Rekomendasi']
    )
    st.dataframe(df_students, use_container_width=True, hide_index=True)
else:
    st.info("Belum ada data siswa.")

# Holland distribution
if completed_tests > 0:
    st.markdown("#### 🎯 Distribusi Tipe Holland")
    
    cursor.execute('SELECT holland_scores FROM test_results')
    holland_data = cursor.fetchall()
    
    holland_totals = {
        'Realistic': 0, 'Investigative': 0, 'Artistic': 0,
        'Social': 0, 'Enterprising': 0, 'Conventional': 0
    }
    
    for row in holland_data:
        scores = json.loads(row[0])
        for holland_type, score in scores.items():
            holland_totals[holland_type] += score
    
    df_holland = pd.DataFrame(
        list(holland_totals.items()),
        columns=['Tipe', 'Total']
    )
    
    fig_holland = px.bar(
        df_holland, x='Tipe', y='Total',
        color='Tipe',
        color_discrete_sequence=['#00d4ff', '#7c3aed', '#10b981', '#f59e0b', '#ef4444', '#6366f1']
    )
    fig_holland.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font_color='#f1f5f9', # Light text
        showlegend=False,
        margin=dict(l=0, r=0, t=20, b=0)
    )
    st.plotly_chart(fig_holland, use_container_width=True)

conn.close()