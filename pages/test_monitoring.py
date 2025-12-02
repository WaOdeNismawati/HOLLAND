import streamlit as st
import pandas as pd
import json
import plotly.express as px
from database.db_manager import DatabaseManager
# from utils.auth import check_login
from utils.config import connection

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


# Main content
st.title("📊 Monitoring Hasil Tes Siswa")
st.markdown("---")

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
    st.stop()

results_data = []
for row in raw_results:
    top_types = json.loads(row[2]) if row[2] else []
    holland_scores = json.loads(row[4]) if row[4] else {}
    anp_results = json.loads(row[6]) if row[6] else None

    results_data.append({
        'full_name': row[0],
        'class_name': row[1],
        'top_3_types': top_types,
        'recommended_major': row[3],
        'holland_scores': holland_scores,
        'completed_at': row[5],
        'anp_results': anp_results,
        'student_id': row[7]
    })

# Statistik umum
st.subheader("📈 Statistik Umum")
majors = [row[3] for row in results_data]
all_top_types = [json.loads(row[2])[0] for row in results_data if row[2] and len(json.loads(row[2])) > 0]

with col1:
    st.metric("Total Hasil Tes", len(results_data))
with col2:
    majors = [row['recommended_major'] for row in results_data]
    most_popular_major = max(set(majors), key=majors.count) if majors else "N/A"
    st.metric("Jurusan Terpopuler", most_popular_major)

with col3:
    all_top_types = [row['top_3_types'][0] for row in results_data if row['top_3_types']]
    most_dominant_type = max(set(all_top_types), key=all_top_types.count) if all_top_types else "N/A"
    st.metric("Tipe Dominan", most_dominant_type)

with col4:
    from datetime import datetime, date
    today_results = [row for row in results_data if row['completed_at'].startswith(str(date.today()))]
    st.metric("Tes Hari Ini", len(today_results))

st.markdown("---")

# --- Filter dan Pencarian ---
st.subheader("🔍 Filter dan Pencarian")
col1, col2, col3 = st.columns(3)
with col1:
    all_classes = list(set([row['class_name'] for row in results_data if row['class_name']]))
    selected_class = st.selectbox("Filter Kelas", options=['Semua'] + sorted(all_classes))

with col2:
    all_majors = list(set([row['recommended_major'] for row in results_data]))
    selected_major = st.selectbox("Filter Jurusan", options=['Semua'] + sorted(all_majors))

with col3:
    search_name = st.text_input("Cari Nama Siswa")

# Apply filters
filtered_data = results_data

if selected_class != 'Semua':
    filtered_data = [row for row in filtered_data if row['class_name'] == selected_class]

if selected_major != 'Semua':
    filtered_data = [row for row in filtered_data if row['recommended_major'] == selected_major]

if search_name:
    filtered_data = [row for row in filtered_data if search_name.lower() in row['full_name'].lower()]

# --- Tabel Hasil ---
st.subheader("📋 Hasil Tes Siswa")
if filtered_data:
    # Prepare data for display
    display_data = []
    for row in filtered_data:
        top_3_types = row['top_3_types']
        display_data.append({
            'Nama': row['full_name'],
            'Kelas': row['class_name'] or 'N/A',
            'Tipe 1': top_3_types[0] if len(top_3_types) > 0 else 'N/A',
            'Tipe 2': top_3_types[1] if len(top_3_types) > 1 else 'N/A',
            'Tipe 3': top_3_types[2] if len(top_3_types) > 2 else 'N/A',
            'Jurusan Rekomendasi': row['recommended_major'],
            'Tanggal Tes': row['completed_at']
        })
    
    df_results = pd.DataFrame(display_data)
    st.dataframe(df_results, use_container_width=True, hide_index=True)
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
            major = row['recommended_major']
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
            top_3 = row['top_3_types']
            if top_3:
                dominant_type = top_3[0]
                dominant_type_counts[dominant_type] = dominant_type_counts.get(dominant_type, 0) + 1
        
        df_types = pd.DataFrame(list(dominant_type_counts.items()), columns=['Tipe Holland', 'Jumlah'])
        
        fig_types = px.pie(df_types, values='Jumlah', names='Tipe Holland',
                          title="Distribusi Tipe Holland Dominan")
        st.plotly_chart(fig_types, use_container_width=True)
    
    # Analisis per kelas
    class_names = [row['class_name'] for row in results_data if row['class_name']]
    if len(set(class_names)) > 1:
        st.subheader("📚 Analisis per Kelas")

        class_analysis = {}
        for row in results_data:
            class_name = row['class_name'] or 'Tidak Ada Kelas'
            if class_name not in class_analysis:
                class_analysis[class_name] = {'total': 0, 'majors': {}}
            class_analysis[class_name]['total'] += 1
            major = row['recommended_major']
            class_analysis[class_name]['majors'][major] = class_analysis[class_name]['majors'].get(major, 0) + 1

        for class_name, data in class_analysis.items():
            with st.expander(f"Kelas {class_name} ({data['total']} siswa)"):
                most_popular = max(data['majors'].items(), key=lambda x: x[1])
                st.write(f"**Jurusan terpopuler:** {most_popular[0]} ({most_popular[1]} siswa)")

                df_class_majors = pd.DataFrame(list(data['majors'].items()), columns=['Jurusan', 'Jumlah'])
                fig_class = px.bar(df_class_majors, x='Jurusan', y='Jumlah',
                                  title=f"Distribusi Jurusan - Kelas {class_name}")
                st.plotly_chart(fig_class, use_container_width=True)

# Detail hasil individual
st.markdown("---")
st.subheader("🔍 Detail Hasil Individual")

if results_data:
    student_options = {
        f"{row['full_name']} ({row['class_name'] or 'N/A'})": i
        for i, row in enumerate(results_data)
    }
    selected_student = st.selectbox("Pilih Siswa untuk Melihat Detail", options=list(student_options.keys()))

    if selected_student:
        student_index = student_options[selected_student]
        student_data = results_data[student_index]

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Informasi Siswa:**")
            st.write(f"- **Nama:** {student_data['full_name']}")
            st.write(f"- **Kelas:** {student_data['class_name'] or 'N/A'}")
            st.write(f"- **Tanggal Tes:** {student_data['completed_at']}")
            st.write(f"- **Jurusan Rekomendasi:** {student_data['recommended_major']}")

        with col2:
            st.write("**3 Tipe Holland Teratas:**")
            top_3_types = student_data['top_3_types']
            for i, holland_type in enumerate(top_3_types, 1):
                st.write(f"{i}. {holland_type}")

        holland_scores = student_data['holland_scores']
        df_student_scores = pd.DataFrame(list(holland_scores.items()), columns=['Tipe Holland', 'Skor'])
        df_student_scores = df_student_scores.sort_values('Skor', ascending=True)

        fig_student = px.bar(
            df_student_scores,
            x='Skor',
            y='Tipe Holland',
            orientation='h',
            title=f"Profil Holland - {student_data['full_name']}",
            color='Skor',
            color_continuous_scale='plasma'
        )
        st.plotly_chart(fig_student, use_container_width=True)

        st.markdown("### 📘 Detail Perhitungan")
        tab_holland, tab_anp, tab_download = st.tabs([
            "📊 Holland Detail",
            "🧠 ANP Detail",
            "⬇️ Unduh Detail"
        ])

        with tab_holland:
            st.write("#### Skor RIASEC Lengkap")
            st.table(df_student_scores.sort_values('Tipe Holland'))
            st.write("#### Penjelasan")
            st.info("Nilai di atas merupakan hasil normalisasi dari semua jawaban siswa per dimensi RIASEC.")

        with tab_anp:
            anp_data = student_data.get('anp_results') or {}
            if not anp_data:
                st.warning("Data ANP belum tersedia untuk siswa ini.")
            else:
                calc_details = anp_data.get('calculation_details', {})
                criteria_priorities = calc_details.get('criteria_priorities', {})
                pairwise_matrix = calc_details.get('pairwise_matrix', [])
                top_majors = anp_data.get('top_5_majors', [])

                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("Total Jurusan Dianalisis", anp_data.get('total_analyzed', 0))
                with col_b:
                    cr_value = calc_details.get('consistency_ratio', 0.0)
                    st.metric("Consistency Ratio", f"{cr_value:.4f}")

                if criteria_priorities:
                    priorities_df = pd.DataFrame([
                        {'Kriteria': k, 'Bobot': v, 'Persentase': v * 100}
                        for k, v in criteria_priorities.items()
                    ]).sort_values('Bobot', ascending=False)
                    st.write("#### Bobot Prioritas Kriteria")
                    st.dataframe(priorities_df, hide_index=True, use_container_width=True)

                if pairwise_matrix:
                    riasec_labels = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
                    pairwise_df = pd.DataFrame(pairwise_matrix, columns=riasec_labels, index=riasec_labels)
                    st.write("#### Matriks Perbandingan Kriteria (Saaty Scale)")
                    st.dataframe(pairwise_df.style.format("{:.3f}"))

                if top_majors:
                    st.write("#### Detil Alternatif (Top 5 Jurusan)")
                    normalized_entries = []
                    for entry in top_majors:
                        if isinstance(entry, dict):
                            normalized_entries.append(entry)
                        elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                            data = entry[1] if isinstance(entry[1], dict) else {}
                            data['major_name'] = entry[0]
                            normalized_entries.append(data)

                    ranking_rows = []
                    for idx, info in enumerate(normalized_entries, 1):
                        ranking_rows.append({
                            'Rank': idx,
                            'Jurusan': info.get('major_name', 'N/A'),
                            'Skor ANP': info.get('anp_score', 0.0)
                        })
                    if ranking_rows:
                        ranking_df = pd.DataFrame(ranking_rows)
                        st.dataframe(ranking_df, hide_index=True, use_container_width=True)

                    for info in normalized_entries:
                        with st.expander(f"Detail {info.get('major_name', 'Jurusan')}"):
                            criteria_weights = info.get('criteria_weights', {})
                            if criteria_weights:
                                cw_df = pd.DataFrame([
                                    {'Kriteria': k, 'Kontribusi': v}
                                    for k, v in criteria_weights.items()
                                ]).sort_values('Kontribusi', ascending=False)
                                st.write("Kontribusi Kriteria terhadap jurusan ini:")
                                st.table(cw_df)
                            profile = info.get('riasec_profile', {})
                            if profile:
                                st.write("Profil RIASEC Jurusan:")
                                st.json(profile)

        with tab_download:
            report_payload = {
                'student': {
                    'name': student_data['full_name'],
                    'class': student_data['class_name'],
                    'completed_at': student_data['completed_at'],
                    'recommended_major': student_data['recommended_major']
                },
                'top_3_types': student_data['top_3_types'],
                'holland_scores': student_data['holland_scores'],
                'anp_results': student_data.get('anp_results')
            }
            report_bytes = json.dumps(report_payload, indent=2).encode('utf-8')
            st.download_button(
                label="📄 Download Detail Hasil (JSON)",
                data=report_bytes,
                file_name=f"hasil_detail_{student_data['full_name'].replace(' ', '_').lower()}.json",
                mime="application/json"
            )

conn.close()