import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.auth import check_login
from utils.timezone import convert_utc_to_local
from utils.config import connection
from components.sidebar import render_sidebar
from utils.styles import apply_dark_theme, get_chart_color_scheme

st.set_page_config(page_title="Hasil Tes", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

# Apply dark theme
apply_dark_theme()

# Render sidebar
st.session_state.current_page = 'student_results'
render_sidebar()

# Cek login & koneksi database
check_login()
conn = connection()

if st.session_state.role != 'student':
    st.error("Akses ditolak! Halaman ini hanya untuk siswa.")
    st.stop()

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
top_3_types = json.loads(result[2]) if isinstance(result[2], str) else result[2]
recommended_major = result[3]
completed_at = result[4]

# ==========================================
# EXTRACT DATA FROM NESTED STRUCTURE
# ==========================================
# Get ANP weights from nested structure
anp_weights = anp_results.get('anp_weights', {})

if not anp_weights and 'anp_results' in anp_results:
    nested = anp_results.get('anp_results', {})
    
    # Try direct criteria_priorities first
    anp_weights = nested.get('criteria_priorities', {})
    
    # If not found, try in calculation_details
    if not anp_weights:
        if 'calculation_details' in nested:
            calc_details_nested = nested.get('calculation_details', {})
            if 'criteria_priorities' in calc_details_nested:
                anp_weights = calc_details_nested.get('criteria_priorities', {})
                # Force update to ensure it's not empty
                if not anp_weights:
                    anp_weights = calc_details_nested['criteria_priorities']

# Debug sudah selesai - extraction logic bekerja dengan baik!

# Get calculation details
calc_details = anp_results.get('anp_results', {}) if 'anp_results' in anp_results else anp_results

# Get rankings from nested structure  
major_rankings = anp_results.get('major_rankings', [])
if not major_rankings and 'anp_results' in anp_results:
    nested_rankings = anp_results.get('anp_results', {}).get('ranked_majors', [])
    major_rankings = [[item[0], item[1]['anp_score']] for item in nested_rankings if len(item) >= 2]

# Extract consistency_ratio for display
consistency_ratio = None
is_consistent = False

if 'anp_results' in anp_results and isinstance(anp_results.get('anp_results'), dict):
    nested = anp_results['anp_results']
    if 'calculation_details' in nested and isinstance(nested['calculation_details'], dict):
        calc_details_nested = nested['calculation_details']
        consistency_ratio = calc_details_nested.get('consistency_ratio')
        is_consistent = calc_details_nested.get('is_consistent', False)
    if consistency_ratio is None:
        consistency_ratio = nested.get('consistency_ratio')
        is_consistent = nested.get('is_consistent', False)

if consistency_ratio is None and calc_details:
    consistency_ratio = calc_details.get('consistency_ratio')
    is_consistent = calc_details.get('is_consistent', False)


# Get normalized scores (0-1) from ANP results
normalized_0_1 = anp_results.get('student_riasec_profile', {})
if not normalized_0_1:
    max_score = max(holland_scores.values()) if holland_scores else 1
    normalized_0_1 = {k: v / max_score for k, v in holland_scores.items()}

# For visualization only: scale to 0-10 for better readability
normalized_visual = {k: v * 10 for k, v in normalized_0_1.items()}

# Header hasil
st.success(f"✅ Tes diselesaikan pada: {convert_utc_to_local(completed_at)}")

# --- Tampilan Hasil ---
st.subheader("🎯 Rekomendasi Jurusan Terbaik")
st.success(f"**🏆 {recommended_major}**")

st.markdown("---")

# 3 Tipe kepribadian teratas
st.subheader("🏆 3 Tipe Kepribadian Teratas")

col1, col2, col3 = st.columns(3)

holland_descriptions = {
    'Realistic': {
        'icon': '🔧',
        'title': 'Realistic',
        'desc': 'Praktis, suka bekerja dengan tangan dan alat',
        'color': '#1a3a52'
    },
    'Investigative': {
        'icon': '🔬', 
        'title': 'Investigative',
        'desc': 'Analitis, suka memecahkan masalah kompleks',
        'color': '#1a3a52'
    },
    'Artistic': {
        'icon': '🎨',
        'title': 'Artistic', 
        'desc': 'Kreatif, suka berkarya seni dan berekspresi',
        'color': '#1a3a52'
    },
    'Social': {
        'icon': '👥',
        'title': 'Social',
        'desc': 'Suka membantu dan berinteraksi dengan orang',
        'color': '#1a3a52'
    },
    'Enterprising': {
        'icon': '💼',
        'title': 'Enterprising',
        'desc': 'Suka memimpin, berbisnis, dan mengambil risiko',
        'color': '#1a3a52'
    },
    'Conventional': {
        'icon': '📊',
        'title': 'Conventional',
        'desc': 'Terorganisir, suka bekerja dengan data dan sistem',
        'color': '#1a3a52'
    }
}

columns = [col1, col2, col3]
for i, holland_type in enumerate(top_3_types):
    with columns[i]:
        desc = holland_descriptions.get(holland_type, {
            'icon': '📌',
            'title': holland_type,
            'desc': 'Tipe Holland',
            'color': '#666666'
        })
        score = holland_scores.get(holland_type, 0)
        
        st.markdown(f"""
        <div style="padding: 15px; text-align: center;">
            <div style="font-size: 2em;">{desc.get('icon', '📌')}</div>
            <h4 style="margin: 10px 0 5px 0; color: #ffffff;">#{i+1} {desc.get('title', holland_type)}</h4>
            <p style="font-size: 0.9em; color: #cbd5e0; margin: 5px 0;">{desc.get('desc', '')}</p>
            <div style="background-color: #1a3a52; color: white; padding: 5px; border-radius: 5px; margin-top: 10px;">
                <strong>Skor: {score}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

st.markdown("---")

# ========================================
# ANP CALCULATION PROCESS VISUALIZATION
# ========================================
if anp_results and isinstance(anp_results, dict):
    st.subheader("🔬 Proses Perhitungan ANP (Analytic Network Process)")
    
    # Tabs untuk berbagai aspek perhitungan
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Ringkasan Hasil", 
        "⚖️ Bobot Kriteria", 
        "📈 Skor Holland",
        "🏆 Ranking Lengkap"
    ])
    
    # TAB 1: Ringkasan Hasil
    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Jurusan Dianalisis",
                len(major_rankings) if major_rankings else 0,
                help="Total jurusan yang dianalisis"
            )
        
        with col2:
            st.metric(
                "Consistency Ratio",
                f"{consistency_ratio:.4f}" if consistency_ratio is not None else "N/A",
                "✓ Konsisten" if is_consistent else ("⚠ Perlu Review" if consistency_ratio and consistency_ratio >= 0.1 else ""),
                help="CR < 0.1 dianggap konsisten (Saaty)"
            )
        
        with col3:
            st.metric(
                "Metode",
                "ANP Murni",
                help="ANP + Inner Dependency + Supermatrix"
            )
        
        st.markdown("---")
        
        # Penjelasan metodologi
        st.success("""
        **🎯 ANP dengan Inner Dependency + Alternative Similarity**
        
        Sistem ini menggunakan metode ANP lengkap sesuai teori Saaty:
        
        1. **Pairwise Comparison Matrix** (6×6)
           - Membandingkan kriteria RIASEC berdasarkan skor siswa
           - Dimodifikasi dengan **Inner Dependency** dari Holland Hexagon
           - Menghasilkan Consistency Ratio (CR) yang valid
        
        2. **Eigenvalue Method**
           - Menghitung bobot prioritas setiap kriteria RIASEC
           - Menggunakan principal eigenvector dari pairwise matrix
        
        3. **Supermatrix Construction** (4 blok)
           - **W₁₁** Kriteria×Kriteria: Inner dependency antar tipe RIASEC
           - **W₂₁** Alternatif×Kriteria: Profil jurusan × skor siswa
           - **W₁₂** Kriteria×Alternatif: Feedback loop
           - **W₂₂** Alternatif×Alternatif: **Cosine Similarity** antar profil jurusan
        
        4. **Limit Supermatrix**
           - Iterasi hingga konvergen (maks 100 iterasi)
           - Menghasilkan prioritas akhir untuk setiap jurusan
        
        **Keunggulan:** Metodologi ANP lengkap, mempertimbangkan hubungan antar kriteria DAN antar alternatif!
        """)
    
    # TAB 2: Bobot Kriteria
    with tab2:
        st.write("### 🎯 Bobot Prioritas Kriteria RIASEC")
        
        if anp_weights:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Bar chart bobot kriteria
                criteria_df = pd.DataFrame([
                    {'Kriteria': k, 'Bobot': v} 
                    for k, v in anp_weights.items()
                ]).sort_values('Bobot', ascending=True)
                
                fig = px.bar(
                    criteria_df,
                    x='Bobot',
                    y='Kriteria',
                    orientation='h',
                    title='Distribusi Bobot Kriteria ANP',
                    color='Bobot',
                    color_continuous_scale=[[0, '#1a1a2e'], [0.5, '#16213e'], [1, '#1a3a52']],
                    template='plotly_dark'
                )
                fig.update_layout(
                    height=400,
                    paper_bgcolor='rgba(26, 26, 46, 0.5)',
                    plot_bgcolor='rgba(22, 33, 62, 0.3)',
                    font_color='#ffffff'
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.write("**📊 Tabel Bobot**")
                df_weights = pd.DataFrame([
                    {
                        'Kriteria': k, 
                        'Bobot': f"{v:.4f}",
                        '%': f"{v*100:.1f}%"
                    } 
                    for k, v in anp_weights.items()
                ])
                st.dataframe(df_weights, hide_index=True, use_container_width=True)
        else:
            st.warning("Data bobot ANP tidak tersedia")
    
    # TAB 3: Skor Holland
    with tab3:
        st.write("### 📊 Skor RIASEC Anda")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**🔢 Skor Mentah**")
            # Bar chart skor mentah
            fig_raw = go.Figure(data=[go.Bar(
                x=list(holland_scores.keys()),
                y=list(holland_scores.values()),
                marker_color='#1a3a52',
                text=list(holland_scores.values()),
                textposition='auto'
            )])
            fig_raw.update_layout(
                title="Skor Holland (Raw)",
                height=350,
                showlegend=False,
                paper_bgcolor='rgba(26, 26, 46, 0.5)',
                plot_bgcolor='rgba(22, 33, 62, 0.3)',
                font_color='#ffffff',
                template='plotly_dark'
            )
            st.plotly_chart(fig_raw, use_container_width=True)
        
        with col2:
            st.write("**📏 Skor Normalized (0-1 untuk ANP)**")
            # Radar chart normalized
            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=list(normalized_0_1.values()),
                theta=list(normalized_0_1.keys()),
                fill='toself',
                name='Profil Anda',
                line_color='#1a3a52',
                fillcolor='rgba(26, 58, 82, 0.5)'
            ))
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 1], gridcolor='rgba(255,255,255,0.2)'),
                    bgcolor='rgba(22, 33, 62, 0.3)'
                ),
                title="Profil RIASEC (Skala 0-1)",
                height=350,
                paper_bgcolor='rgba(26, 26, 46, 0.5)',
                font_color='#ffffff',
                template='plotly_dark'
            )
            st.plotly_chart(fig_radar, use_container_width=True)
        
        st.markdown("---")
        
        # Tabel skor lengkap
        st.write("**📋 Tabel Skor Lengkap**")
        df_scores = pd.DataFrame([
            {
                'Tipe': k,
                'Icon': holland_descriptions.get(k, {}).get('icon', '📌'),
                'Skor Raw': holland_scores.get(k, 0),
                'Normalized (0-1)': f"{normalized_0_1.get(k, 0):.3f}",
                'Deskripsi': holland_descriptions.get(k, {}).get('desc', '-')
            }
            for k in holland_scores.keys()
        ])
        st.dataframe(df_scores, hide_index=True, use_container_width=True)
        
        st.info("""
        💡 **Catatan Normalisasi:**
        - Skor **Raw** adalah total jawaban per tipe RIASEC
        - Skor **Normalized (0-1)** digunakan untuk perhitungan ANP
        - Dalam ANP, skor ini digunakan untuk membuat **pairwise comparison matrix** dengan skala Saaty (1-9)
        - Ratio antar skor otomatis di-clip ke range 1/9 hingga 9 sesuai standar Saaty
        """)
    
    # TAB 4: Ranking Lengkap
    with tab4:
        st.write("### 🏆 Ranking Jurusan Lengkap")
        
        if major_rankings:
            st.info(f"📌 Menampilkan Top {min(len(major_rankings), 20)} dari {len(major_rankings)} jurusan")
            
            # Top 20
            top_20 = major_rankings[:20]
            df_majors = pd.DataFrame(top_20, columns=['Jurusan', 'ANP Score'])
            df_majors.index = range(1, len(df_majors) + 1)
            df_majors['ANP Score'] = df_majors['ANP Score'].round(4)
            
            # Styling
            st.dataframe(
                df_majors.style.background_gradient(subset=['ANP Score'], cmap='Greens'),
                use_container_width=True
            )
            
            # Bar chart horizontal Top 10
            st.write("**📊 Visualisasi Top 10 Jurusan**")
            top_10 = major_rankings[:10]
            fig_majors = go.Figure(data=[go.Bar(
                y=[item[0] for item in top_10],
                x=[item[1] for item in top_10],
                orientation='h',
                marker_color='#1a3a52',
                text=[f"{item[1]:.4f}" for item in top_10],
                textposition='auto'
            )])
            fig_majors.update_layout(
                title="Top 10 Jurusan (ANP Score)",
                xaxis_title="ANP Score",
                yaxis_title="Jurusan",
                height=500,
                yaxis={'categoryorder':'total ascending'},
                paper_bgcolor='rgba(26, 26, 46, 0.5)',
                plot_bgcolor='rgba(22, 33, 62, 0.3)',
                font_color='#ffffff',
                template='plotly_dark'
            )
            st.plotly_chart(fig_majors, use_container_width=True)
        else:
            st.warning("Data ranking jurusan tidak tersedia")

st.markdown("---")

# =============================================
# TAMPILKAN RIWAYAT JAWABAN TES
# =============================================
with st.expander("📋 Lihat Riwayat Jawaban Tes", expanded=False):
    st.subheader("📝 Jawaban Tes Anda")
    
    # Ambil jawaban siswa dari database
    conn_answers = connection()
    cursor_answers = conn_answers.cursor()
    
    cursor_answers.execute('''
        SELECT 
            sa.question_order,
            q.question_text,
            q.holland_type,
            sa.answer,
            sa.response_time
        FROM student_answers sa
        JOIN questions q ON sa.question_id = q.id
        WHERE sa.student_id = ?
        ORDER BY sa.question_order ASC
    ''', (st.session_state.user_id,))
    
    answers_data = cursor_answers.fetchall()
    conn_answers.close()
    
    if answers_data:
        # Label untuk nilai jawaban
        answer_descriptions = {
            1: "Sangat Tidak Setuju",
            2: "Tidak Setuju",
            3: "Netral",
            4: "Setuju",
            5: "Sangat Setuju"
        }
        
        # Icon untuk tipe Holland
        holland_icons_answers = {
            'Realistic': '🔧',
            'Investigative': '🔬',
            'Artistic': '🎨',
            'Social': '👥',
            'Enterprising': '💼',
            'Conventional': '📊'
        }
        
        # Buat DataFrame untuk ditampilkan
        df_answers = pd.DataFrame(answers_data, columns=[
            'No', 'Pertanyaan', 'Tipe Holland', 'Nilai', 'Waktu (detik)'
        ])
        
        # Tambahkan icon ke tipe Holland
        df_answers['Tipe Holland'] = df_answers['Tipe Holland'].apply(
            lambda x: f"{holland_icons_answers.get(x, '📌')} {x}"
        )
        
        # Tambahkan deskripsi jawaban
        df_answers['Jawaban'] = df_answers['Nilai'].apply(
            lambda x: f"{x} - {answer_descriptions.get(x, 'Unknown')}"
        )
        
        # Tampilkan statistik singkat
        col_stat1, col_stat2, col_stat3 = st.columns(3)
        with col_stat1:
            st.metric("Total Soal Dijawab", len(df_answers))
        with col_stat2:
            avg_answer = df_answers['Nilai'].mean()
            st.metric("Rata-rata Nilai", f"{avg_answer:.2f}")
        with col_stat3:
            avg_time = sum([x[4] for x in answers_data if x[4]]) / len(answers_data)
            st.metric("Rata-rata Waktu", f"{avg_time:.1f}s")
        
        st.markdown("---")
        
        # Tampilkan tabel jawaban (tanpa kolom Nilai asli)
        df_display = df_answers[['No', 'Pertanyaan', 'Tipe Holland', 'Jawaban', 'Waktu (detik)']]
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Ringkasan per tipe Holland
        st.markdown("---")
        st.write("**📊 Ringkasan Jawaban per Tipe Holland:**")
        
        summary_data = []
        for holland_type in ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']:
            type_answers = [x[3] for x in answers_data if x[2] == holland_type]
            if type_answers:
                icon = holland_icons_answers.get(holland_type, '📌')
                total = sum(type_answers)
                avg = sum(type_answers) / len(type_answers)
                summary_data.append({
                    'Tipe': f"{icon} {holland_type}",
                    'Jumlah Soal': len(type_answers),
                    'Total Skor': total,
                    'Rata-rata': f"{avg:.2f}"
                })
        
        df_summary = pd.DataFrame(summary_data)
        st.dataframe(df_summary, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data jawaban tersimpan.")

st.markdown("---")

# Footer - Informasi Tambahan
with st.expander("ℹ️ Tentang Metode Perhitungan"):
    st.markdown("""
    ### 📚 Referensi Ilmiah
    
    - **Holland's Theory of Career Choice** (John L. Holland, 1959)
    - **Analytical Network Process** (Thomas L. Saaty, 1996)

    
    ### 💡 Tips Memilih Jurusan
    
    Hasil ini adalah rekomendasi berdasarkan minat Anda. Pertimbangkan juga:
    - ✅ Bakat dan kemampuan akademik
    - ✅ Passion dan minat jangka panjang
    - ✅ Peluang karir dan prospek masa depan
    - ✅ Kondisi ekonomi dan keluarga
    - ✅ Fasilitas dan akreditasi kampus
    """)

st.caption("💡 Gunakan hasil ini sebagai panduan dalam memilih jurusan yang tepat untuk masa depan Anda!")
