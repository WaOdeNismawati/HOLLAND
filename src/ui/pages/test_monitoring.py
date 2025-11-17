import json

import pandas as pd
import plotly.express as px
import streamlit as st

from src.core.config import connection

# # Cek login
# check_login()
# # Database connection
# db_manager = DatabaseManager()
# conn = db_manager.get_connection()
conn = connection()


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

if not results_data:
    st.info("Belum ada siswa yang menyelesaikan tes.")
    st.stop()

# Statistik umum
st.subheader("📈 Statistik Umum")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Hasil Tes", len(results_data))

with col2:
    # Jurusan paling populer
    majors = [row[3] for row in results_data]
    most_popular_major = max(set(majors), key=majors.count) if majors else "N/A"
    st.metric("Jurusan Terpopuler", most_popular_major)

with col3:
    # Tipe Holland paling dominan
    all_top_types = []
    for row in results_data:
        top_3 = json.loads(row[2])
        if top_3:
            all_top_types.append(top_3[0])  # Ambil tipe pertama
    
    most_dominant_type = max(set(all_top_types), key=all_top_types.count) if all_top_types else "N/A"
    st.metric("Tipe Dominan", most_dominant_type)

with col4:
    # Rata-rata hari ini
    from datetime import datetime, date
    today_results = [row for row in results_data if row[5].startswith(str(date.today()))]
    st.metric("Tes Hari Ini", len(today_results))

st.markdown("---")

# Filter dan pencarian
st.subheader("🔍 Filter dan Pencarian")

col1, col2, col3 = st.columns(3)

with col1:
    # Filter berdasarkan kelas
    all_classes = list(set([row[1] for row in results_data if row[1]]))
    selected_class = st.selectbox("Filter Kelas", options=['Semua'] + sorted(all_classes))

with col2:
    # Filter berdasarkan jurusan rekomendasi
    all_majors = list(set([row[3] for row in results_data]))
    selected_major = st.selectbox("Filter Jurusan", options=['Semua'] + sorted(all_majors))

with col3:
    # Pencarian nama
    search_name = st.text_input("Cari Nama Siswa")

# Apply filters
filtered_data = results_data

if selected_class != 'Semua':
    filtered_data = [row for row in filtered_data if row[1] == selected_class]

if selected_major != 'Semua':
    filtered_data = [row for row in filtered_data if row[3] == selected_major]

if search_name:
    filtered_data = [row for row in filtered_data if search_name.lower() in row[0].lower()]

st.markdown("---")

# Tabel hasil tes
st.subheader("📋 Hasil Tes Siswa")

if filtered_data:
    # Prepare data for display
    display_data = []
    for row in filtered_data:
        top_3_types = json.loads(row[2])
        display_data.append({
            'Nama': row[0],
            'Kelas': row[1] or 'N/A',
            'Tipe 1': top_3_types[0] if len(top_3_types) > 0 else 'N/A',
            'Tipe 2': top_3_types[1] if len(top_3_types) > 1 else 'N/A',
            'Tipe 3': top_3_types[2] if len(top_3_types) > 2 else 'N/A',
            'Jurusan Rekomendasi': row[3],
            'Tanggal Tes': row[5]
        })
    
    df_results = pd.DataFrame(display_data)
    st.dataframe(df_results, use_container_width=True)
    
    # Download CSV
    csv = df_results.to_csv(index=False)
    st.download_button(
        label="📥 Download Data CSV",
        data=csv,
        file_name="hasil_tes_minat_bakat.csv",
        mime="text/csv"
    )
    
else:
    st.info("Tidak ada data yang sesuai dengan filter.")

st.markdown("---")

# Analisis dan visualisasi
st.subheader("📊 Analisis Data")

if results_data:
    col1, col2 = st.columns(2)
    
    with col1:
        # Distribusi jurusan rekomendasi
        major_counts = {}
        for row in results_data:
            major = row[3]
            major_counts[major] = major_counts.get(major, 0) + 1
        
        df_majors = pd.DataFrame(list(major_counts.items()), columns=['Jurusan', 'Jumlah'])
        df_majors = df_majors.sort_values('Jumlah', ascending=True)
        
        fig_majors = px.bar(df_majors, x='Jumlah', y='Jurusan', orientation='h',
                           title="Distribusi Jurusan Rekomendasi",
                           color='Jumlah', color_continuous_scale='viridis')
        st.plotly_chart(fig_majors, use_container_width=True)
    
    with col2:
        # Distribusi tipe Holland dominan
        dominant_type_counts = {}
        for row in results_data:
            top_3 = json.loads(row[2])
            if top_3:
                dominant_type = top_3[0]
                dominant_type_counts[dominant_type] = dominant_type_counts.get(dominant_type, 0) + 1
        
        df_types = pd.DataFrame(list(dominant_type_counts.items()), columns=['Tipe Holland', 'Jumlah'])
        
        fig_types = px.pie(df_types, values='Jumlah', names='Tipe Holland',
                          title="Distribusi Tipe Holland Dominan")
        st.plotly_chart(fig_types, use_container_width=True)
    
    # Analisis per kelas
    if len(set([row[1] for row in results_data if row[1]])) > 1:
        st.subheader("📚 Analisis per Kelas")
        
        class_analysis = {}
        for row in results_data:
            class_name = row[1] or 'Tidak Ada Kelas'
            if class_name not in class_analysis:
                class_analysis[class_name] = {'total': 0, 'majors': {}}
            
            class_analysis[class_name]['total'] += 1
            major = row[3]
            class_analysis[class_name]['majors'][major] = class_analysis[class_name]['majors'].get(major, 0) + 1
        
        # Tampilkan analisis per kelas
        for class_name, data in class_analysis.items():
            with st.expander(f"Kelas {class_name} ({data['total']} siswa)"):
                most_popular = max(data['majors'].items(), key=lambda x: x[1])
                st.write(f"**Jurusan terpopuler:** {most_popular[0]} ({most_popular[1]} siswa)")
                
                # Mini chart untuk kelas ini
                df_class_majors = pd.DataFrame(list(data['majors'].items()), columns=['Jurusan', 'Jumlah'])
                fig_class = px.bar(df_class_majors, x='Jurusan', y='Jumlah',
                                  title=f"Distribusi Jurusan - Kelas {class_name}")
                st.plotly_chart(fig_class, use_container_width=True)

# Detail hasil individual
st.markdown("---")
st.subheader("🔍 Detail Hasil Individual")

if results_data:
    # Pilih siswa untuk melihat detail
    student_options = {f"{row[0]} ({row[1] or 'N/A'})": i for i, row in enumerate(results_data)}
    selected_student = st.selectbox("Pilih Siswa untuk Melihat Detail", options=list(student_options.keys()))
    
    if selected_student:
        student_index = student_options[selected_student]
        student_data = results_data[student_index]
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Informasi Siswa:**")
            st.write(f"- **Nama:** {student_data[0]}")
            st.write(f"- **Kelas:** {student_data[1] or 'N/A'}")
            st.write(f"- **Tanggal Tes:** {student_data[5]}")
            st.write(f"- **Jurusan Rekomendasi:** {student_data[3]}")
        
        with col2:
            st.write("**3 Tipe Holland Teratas:**")
            top_3_types = json.loads(student_data[2])
            for i, holland_type in enumerate(top_3_types, 1):
                st.write(f"{i}. {holland_type}")
        
        # Skor Holland detail
        holland_scores = json.loads(student_data[4])
        df_student_scores = pd.DataFrame(list(holland_scores.items()), columns=['Tipe Holland', 'Skor'])
        df_student_scores = df_student_scores.sort_values('Skor', ascending=True)
        
        fig_student = px.bar(df_student_scores, x='Skor', y='Tipe Holland', orientation='h',
                           title=f"Profil Holland - {student_data[0]}",
                           color='Skor', color_continuous_scale='plasma')
        st.plotly_chart(fig_student, use_container_width=True)

conn.close()