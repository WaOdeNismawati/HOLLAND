import streamlit as st
import pandas as pd
import json
import plotly.express as px
from database.db_manager import DatabaseManager
from utils.auth import check_login
from utils.config import connection
from datetime import datetime, date
from components.sidebar import render_sidebar
from utils.styles import apply_dark_theme, get_chart_color_scheme

# Page config (letakkan dulu sebelum elemen UI lain)
st.set_page_config(page_title="Monitoring Hasil Tes", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# Apply dark theme
apply_dark_theme()

# Render sidebar
st.session_state.current_page = 'test_monitoring'
render_sidebar()

# Database connection
# db_manager = DatabaseManager()
# conn = db_manager.get_connection()
conn = connection()

# Pastikan session_state.role ada (jangan crash kalau belum di-set)
user_role = st.session_state.get("role", None)
if user_role != 'admin':
    st.error("Akses ditolak! Halaman ini hanya untuk admin.")
    st.stop()

cursor = conn.cursor()

# Ambil data hasil tes
cursor.execute('''
    SELECT u.full_name, u.class_name, tr.top_3_types, tr.recommended_major,
           tr.holland_scores, tr.completed_at, tr.anp_results, tr.student_id
    FROM test_results tr
    JOIN users u ON tr.student_id = u.id
    ORDER BY tr.completed_at DESC
''')

raw_results = cursor.fetchall()

if not raw_results:
    st.info("Belum ada siswa yang menyelesaikan tes.")
    conn.close()
    st.stop()

# Normalisasi hasil dari DB ke list of dict
results_data = []
for row in raw_results:
    # row indices based on SELECT order
    full_name = row[0]
    class_name = row[1]
    raw_top3 = row[2]
    recommended_major = row[3]
    raw_scores = row[4]
    completed_at_raw = row[5]
    raw_anp = row[6]
    student_id = row[7] if len(row) > 7 else None

    # top_3_types stored sebagai JSON string di DB (mis. '["Realistic","Investigative",...]')
    try:
        top_types = json.loads(raw_top3) if raw_top3 else []
    except Exception:
        # fallback: jika sudah list
        top_types = raw_top3 if isinstance(raw_top3, (list, tuple)) else []

    # holland_scores mungkin JSON string atau dict
    try:
        holland_scores = json.loads(raw_scores) if raw_scores else {}
    except Exception:
        holland_scores = raw_scores if isinstance(raw_scores, dict) else {}

    # anp_results mungkin JSON string atau dict
    try:
        anp_results = json.loads(raw_anp) if raw_anp else None
    except Exception:
        anp_results = raw_anp if isinstance(raw_anp, dict) else None

    # completed_at: simpan sebagai string untuk ditampilkan, tapi coba parse untuk filtering tanggal
    completed_at_str = str(completed_at_raw) if completed_at_raw is not None else ""

    # also try to produce a parsed date for easier comparisons
    parsed_completed_at = None
    if isinstance(completed_at_raw, (int, float)):
        # unix timestamp?
        try:
            parsed_completed_at = datetime.fromtimestamp(int(completed_at_raw))
        except Exception:
            parsed_completed_at = None
    else:
        # try ISO parse
        try:
            parsed_completed_at = datetime.fromisoformat(completed_at_str)
        except Exception:
            # try common sqlite format
            try:
                parsed_completed_at = datetime.strptime(completed_at_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                parsed_completed_at = None

    results_data.append({
        'full_name': full_name,
        'class_name': class_name,
        'top_3_types': top_types,
        'recommended_major': recommended_major,
        'holland_scores': holland_scores,
        'completed_at': completed_at_str,
        'completed_at_dt': parsed_completed_at,  # bisa None
        'anp_results': anp_results,
        'student_id': student_id
    })

# Statistik umum
st.subheader("📈 Statistik Umum")
# buat 4 kolom untuk metric
col1, col2, col3, col4 = st.columns(4)

# Total hasil tes
with col1:
    st.metric("Total Hasil Tes", len(results_data))

# Jurusan terpopuler
with col2:
    majors = [row.get('recommended_major') or "N/A" for row in results_data]
    majors_clean = [m for m in majors if m and m != "N/A"]
    most_popular_major = max(set(majors_clean), key=majors_clean.count) if majors_clean else "N/A"
    st.metric("Jurusan Terpopuler", most_popular_major)

# Tipe dominan (top tipe pertama)
with col3:
    all_top_types = [
        row['top_3_types'][0]
        for row in results_data
        if row.get('top_3_types') and isinstance(row['top_3_types'], (list, tuple)) and len(row['top_3_types']) > 0
    ]
    most_dominant_type = max(set(all_top_types), key=all_top_types.count) if all_top_types else "N/A"
    st.metric("Tipe Dominan", most_dominant_type)

# Tes hari ini
with col4:
    today = date.today()
    today_results = []
    for row in results_data:
        dt = row.get('completed_at_dt')
        if dt:
            if dt.date() == today:
                today_results.append(row)
        else:
            # fallback: jika completed_at string dimulai dengan YYYY-MM-DD cocok
            s = row.get('completed_at', '')
            if s.startswith(str(today)):
                today_results.append(row)
    st.metric("Tes Hari Ini", len(today_results))

st.markdown("---")

# --- Filter dan Pencarian ---
st.subheader("🔍 Filter dan Pencarian")
filter_col1, filter_col2, filter_col3 = st.columns(3)

with filter_col1:
    all_classes = sorted(list({row['class_name'] for row in results_data if row.get('class_name')}))
    selected_class = st.selectbox("Filter Kelas", options=['Semua'] + all_classes)

with filter_col2:
    all_majors = sorted(list({row.get('recommended_major') or 'N/A' for row in results_data}))
    selected_major = st.selectbox("Filter Jurusan", options=['Semua'] + all_majors)

with filter_col3:
    search_name = st.text_input("Cari Nama Siswa")

# Apply filters
filtered_data = results_data.copy()

if selected_class != 'Semua':
    filtered_data = [row for row in filtered_data if row.get('class_name') == selected_class]

if selected_major != 'Semua':
    filtered_data = [row for row in filtered_data if (row.get('recommended_major') or 'N/A') == selected_major]

if search_name:
    filtered_data = [row for row in filtered_data if search_name.lower() in (row.get('full_name') or "").lower()]

# --- Tabel Hasil ---
st.subheader("📋 Hasil Tes Siswa")
if filtered_data:
    # Prepare data for display
    display_data = []
    for row in filtered_data:
        top_3_types = row.get('top_3_types') or []
        display_data.append({
            'Nama': row.get('full_name') or 'N/A',
            'Kelas': row.get('class_name') or 'N/A',
            'Tipe 1': top_3_types[0] if len(top_3_types) > 0 else 'N/A',
            'Tipe 2': top_3_types[1] if len(top_3_types) > 1 else 'N/A',
            'Tipe 3': top_3_types[2] if len(top_3_types) > 2 else 'N/A',
            'Jurusan Rekomendasi': row.get('recommended_major') or 'N/A',
            'Tanggal Tes': row.get('completed_at') or 'N/A'
        })

    df_results = pd.DataFrame(display_data)
    st.dataframe(df_results, use_container_width=True, hide_index=True)
else:
    st.info("Tidak ada data yang sesuai dengan filter.")

st.markdown("---")

# Analisis dan visualisasi
st.subheader("📊 Analisis Data")

if results_data:
    vcol1, vcol2 = st.columns(2)

    with vcol1:
        # Distribusi jurusan rekomendasi
        major_counts = {}
        for row in results_data:
            major = row.get('recommended_major') or 'N/A'
            major_counts[major] = major_counts.get(major, 0) + 1

        df_majors = pd.DataFrame(list(major_counts.items()), columns=['Jurusan', 'Jumlah'])
        df_majors = df_majors.sort_values('Jumlah', ascending=True)

        fig_majors = px.bar(df_majors, x='Jumlah', y='Jurusan', orientation='h',
                           title="Distribusi Jurusan Rekomendasi",
                           color='Jumlah', color_continuous_scale='viridis',
                           template='plotly_dark')
        fig_majors.update_layout(
            paper_bgcolor='rgba(26, 26, 46, 0.5)',
            plot_bgcolor='rgba(22, 33, 62, 0.3)'
        )
        st.plotly_chart(fig_majors, use_container_width=True)

    with vcol2:
        # Distribusi tipe Holland dominan
        dominant_type_counts = {}
        for row in results_data:
            top_3 = row.get('top_3_types') or []
            if top_3:
                dominant_type = top_3[0]
                dominant_type_counts[dominant_type] = dominant_type_counts.get(dominant_type, 0) + 1

        if dominant_type_counts:
            df_types = pd.DataFrame(list(dominant_type_counts.items()), columns=['Tipe Holland', 'Jumlah'])
            fig_types = px.pie(df_types, values='Jumlah', names='Tipe Holland',
                              title="Distribusi Tipe Holland Dominan",
                              template='plotly_dark')
            fig_types.update_layout(
                paper_bgcolor='rgba(26, 26, 46, 0.5)',
                plot_bgcolor='rgba(22, 33, 62, 0.3)'
            )
            st.plotly_chart(fig_types, use_container_width=True)
        else:
            st.info("Belum ada data tipe Holland untuk divisualisasikan.")

    # Analisis per kelas
    class_names = [row.get('class_name') for row in results_data if row.get('class_name')]
    if len(set(class_names)) > 1:
        st.subheader("📚 Analisis per Kelas")

        class_analysis = {}
        for row in results_data:
            class_name = row.get('class_name') or 'Tidak Ada Kelas'
            if class_name not in class_analysis:
                class_analysis[class_name] = {'total': 0, 'majors': {}}
            class_analysis[class_name]['total'] += 1
            major = row.get('recommended_major') or 'N/A'
            class_analysis[class_name]['majors'][major] = class_analysis[class_name]['majors'].get(major, 0) + 1

        for class_name, data in class_analysis.items():
            with st.expander(f"Kelas {class_name} ({data['total']} siswa)"):
                most_popular = max(data['majors'].items(), key=lambda x: x[1])
                st.write(f"**Jurusan terpopuler:** {most_popular[0]} ({most_popular[1]} siswa)")

                df_class_majors = pd.DataFrame(list(data['majors'].items()), columns=['Jurusan', 'Jumlah'])
                fig_class = px.bar(df_class_majors, x='Jurusan', y='Jumlah',
                                  title=f"Distribusi Jurusan - Kelas {class_name}",
                                  template='plotly_dark')
                fig_class.update_layout(
                    paper_bgcolor='rgba(26, 26, 46, 0.5)',
                    plot_bgcolor='rgba(22, 33, 62, 0.3)'
                )
                st.plotly_chart(fig_class, use_container_width=True)

# Detail hasil individual
st.markdown("---")
st.subheader("🔍 Detail Hasil Individual")

if results_data:
    student_options = {
        f"{row.get('full_name')} ({row.get('class_name') or 'N/A'})": i
        for i, row in enumerate(results_data)
    }
    selected_student = st.selectbox("Pilih Siswa untuk Melihat Detail", options=list(student_options.keys()))

    if selected_student:
        student_index = student_options[selected_student]
        student_data = results_data[student_index]

        dcol1, dcol2 = st.columns(2)

        with dcol1:
            st.write("**Informasi Siswa:**")
            st.write(f"- **Nama:** {student_data.get('full_name')}")
            st.write(f"- **Kelas:** {student_data.get('class_name') or 'N/A'}")
            st.write(f"- **Tanggal Tes:** {student_data.get('completed_at') or 'N/A'}")
            st.write(f"- **Jurusan Rekomendasi:** {student_data.get('recommended_major') or 'N/A'}")

        with dcol2:
            st.write("**3 Tipe Holland Teratas:**")
            top_3_types = student_data.get('top_3_types') or []
            if top_3_types:
                for i, holland_type in enumerate(top_3_types, 1):
                    st.write(f"{i}. {holland_type}")
            else:
                st.write("Data tipe Holland tidak tersedia.")

        holland_scores = student_data.get('holland_scores') or {}
        if holland_scores:
            df_student_scores = pd.DataFrame(list(holland_scores.items()), columns=['Tipe Holland', 'Skor'])
            df_student_scores = df_student_scores.sort_values('Skor', ascending=True)

            fig_student = px.bar(
                df_student_scores,
                x='Skor',
                y='Tipe Holland',
                orientation='h',
                title=f"Profil Holland - {student_data.get('full_name')}",
                color='Skor',
                color_continuous_scale='plasma',
                template='plotly_dark'
            )
            fig_student.update_layout(
                paper_bgcolor='rgba(26, 26, 46, 0.5)',
                plot_bgcolor='rgba(22, 33, 62, 0.3)'
            )
            st.plotly_chart(fig_student, use_container_width=True)
        else:
            st.info("Skor Holland tidak tersedia untuk siswa ini.")


# Tutup koneksi DB
conn.close()
