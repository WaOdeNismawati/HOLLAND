import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.core.auth import require_role
from src.core.config import connection_context
from src.shared.timezone import convert_utc_to_local
from src.ui.components.sidebar import sidebar
# # Cek login
# check_login()
# # Database connection
# db_manager = DatabaseManager()
# conn = db_manager.get_connection()

require_role('student')

session = st.session_state
user_id = session.get('user_id')

if user_id is None:
    st.error("Sesi tidak valid. Silakan login kembali.")
    st.stop()

st.set_page_config(page_title="Hasil Tes", page_icon="📊", layout="wide")

# Sidebar
sidebar(title="📊 Hasil Tes")

# Main content
st.title("📊 Hasil Tes Minat Bakat")
st.markdown("---")

with connection_context() as conn:
    cursor = conn.cursor()
    cursor.execute('''
        SELECT top_3_types, recommended_major, holland_scores, anp_results, completed_at
        FROM test_results 
        WHERE student_id = ?
    ''', (user_id,))

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
anp_results = json.loads(result[3]) if result[3] else None
completed_at = result[4]

# PENTING: Pastikan menggunakan holland_scores sebagai sumber data utama
# untuk konsistensi di seluruh halaman
student_profile = holland_scores  # Sumber data utama

# Jika ada data di anp_results, gunakan student_riasec_profile dari sana
# HANYA jika sama dengan holland_scores (untuk validasi)
if anp_results and isinstance(anp_results, dict):
    anp_profile = anp_results.get('student_riasec_profile', {})
    # Validasi: pastikan data konsisten
    if anp_profile and anp_profile != holland_scores:
        st.warning("⚠️ Terdeteksi inkonsistensi data. Menggunakan holland_scores sebagai referensi.")
        # Override dengan holland_scores
        if 'student_riasec_profile' in anp_results:
            anp_results['student_riasec_profile'] = holland_scores

# Header hasil
st.success(f"✅ Tes diselesaikan pada: {convert_utc_to_local(completed_at)}")

# Rekomendasi utama dengan ANP
st.subheader("🎯 Rekomendasi Jurusan Terbaik")
st.markdown(f"""
<div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; border-left: 5px solid #28a745;">
    <h2 style="color: #155724; margin: 0;">🎓 {recommended_major}</h2>
    <p style="color: #155724; margin: 5px 0 0 0;">Rekomendasi terbaik berdasarkan analisis ANP (Analytic Network Process)</p>
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

# ========================================
# ANP CALCULATION PROCESS VISUALIZATION
# ========================================
if anp_results and isinstance(anp_results, dict):
    st.subheader("🔬 Proses Perhitungan ANP (Analytic Network Process)")
    
    calc_details = anp_results.get('calculation_details', {})
    
    # Tabs untuk berbagai aspek perhitungan
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Ringkasan Hasil", 
        "⚖️ Bobot Kriteria", 
        "🔢 Detail Perhitungan",
        "🏆 Ranking Lengkap"
    ])
    
    # TAB 1: Ringkasan Hasil
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Jurusan Dianalisis",
                anp_results.get('total_analyzed', 0),
                help="Total jurusan yang dianalisis ANP"
            )
        
        with col2:
            cr_value = calc_details.get('consistency_ratio', 0)
            is_consistent = calc_details.get('is_consistent', False)
            st.metric(
                "Consistency Ratio",
                f"{cr_value:.4f}",
                "✓ Konsisten" if is_consistent else "⚠ Perlu Review",
                help="CR < 0.1 dianggap konsisten"
            )
        
        with col3:
            st.metric(
                "Iterasi Konvergen",
                calc_details.get('iterations', 0),
                help="Jumlah iterasi hingga supermatrix konvergen"
            )
        
        with col4:
            converged = calc_details.get('converged', False)
            st.metric(
                "Status Konvergensi",
                "✓ Konvergen" if converged else "⚠ Tidak",
                help="Apakah limit supermatrix berhasil konvergen"
            )
        
        st.markdown("---")
        
        # Penjelasan singkat ANP
        st.info("""
        **Analytic Network Process (ANP)** adalah metode pengambilan keputusan multi-kriteria yang:
        - Mempertimbangkan ketergantungan dan feedback antar kriteria
        - Menggunakan pairwise comparison untuk menentukan bobot
        - Menghasilkan ranking yang lebih akurat dibanding metode sederhana
        """)
    
    # TAB 2: Bobot Kriteria
    with tab2:
        st.write("### 🎯 Bobot Prioritas Kriteria RIASEC")
        
        criteria_priorities = calc_details.get('criteria_priorities', {})
        
        if criteria_priorities:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # Bar chart bobot kriteria
                criteria_df = pd.DataFrame([
                    {'Kriteria': k, 'Bobot': v} 
                    for k, v in criteria_priorities.items()
                ]).sort_values('Bobot', ascending=True)
                
                fig_criteria = px.bar(
                    criteria_df, 
                    x='Bobot', 
                    y='Kriteria',
                    orientation='h',
                    color='Bobot',
                    color_continuous_scale='Blues',
                    title="Bobot Prioritas Kriteria"
                )
                fig_criteria.update_layout(height=400)
                st.plotly_chart(fig_criteria, use_container_width=True)
            
            with col2:
                st.write("**Tabel Bobot:**")
                for i, (criterion, weight) in enumerate(
                    sorted(criteria_priorities.items(), key=lambda x: x[1], reverse=True), 1
                ):
                    percentage = weight * 100
                    st.write(f"{i}. **{criterion}**: {weight:.4f} ({percentage:.2f}%)")
        
        st.markdown("---")
        
        st.write("### 📐 Pairwise Comparison Matrix")
        st.info("""
        Matriks perbandingan berpasangan menggunakan **Saaty Scale (1-9)** untuk membandingkan 
        setiap pasang kriteria berdasarkan skor RIASEC Anda.
        """)
        
        pairwise_matrix = calc_details.get('pairwise_matrix', [])
        if pairwise_matrix:
            riasec_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
            pairwise_df = pd.DataFrame(
                pairwise_matrix,
                columns=riasec_types,
                index=riasec_types
            )
            st.dataframe(pairwise_df.style.format("{:.4f}").background_gradient(cmap='RdYlGn', axis=None))
            
            # Consistency check
            cr_value = calc_details.get('consistency_ratio', 0)
            is_consistent = calc_details.get('is_consistent', False)
            
            if is_consistent:
                st.success(f"✅ Matriks konsisten (CR = {cr_value:.4f} < 0.1)")
            else:
                st.warning(f"⚠️ Matriks kurang konsisten (CR = {cr_value:.4f} ≥ 0.1). Hasil tetap valid namun mungkin kurang optimal.")
    
    # TAB 3: Detail Perhitungan
    with tab3:
        st.write("### 🔢 Tahapan Perhitungan ANP")
        
        # Step-by-step explanation
        with st.expander("📝 Step 1: Pairwise Comparison Matrix", expanded=True):
            st.write("""
            - Membandingkan setiap pasangan kriteria RIASEC
            - Menggunakan rasio skor Anda yang dipetakan ke Saaty Scale (1-9)
            - Nilai > 1: kriteria baris lebih penting dari kolom
            - Nilai < 1: kriteria kolom lebih penting dari baris
            """)
            
            if calc_details.get('pairwise_matrix'):
                st.write("**Contoh interpretasi:**")
                riasec_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
                matrix = np.array(calc_details['pairwise_matrix'])
                
                # Show first comparison as example
                st.code(f"""
Perbandingan {riasec_types[0]} vs {riasec_types[1]}:
Nilai = {matrix[0, 1]:.4f}

Interpretasi: {riasec_types[0]} {"lebih penting" if matrix[0, 1] > 1 else "kurang penting"} 
dibanding {riasec_types[1]} dengan rasio {matrix[0, 1]:.2f}:1
                """)
        
        with st.expander("⚖️ Step 2: Priority Vector (Eigenvector)"):
            st.write("""
            - Menghitung vektor eigen utama (principal eigenvector) dari matriks pairwise
            - Vektor ini merepresentasikan bobot/prioritas relatif setiap kriteria
            - Dinormalisasi sehingga total bobot = 1.0
            """)
            
            if criteria_priorities:
                st.write("**Bobot Hasil:**")
                total = sum(criteria_priorities.values())
                for criterion, weight in criteria_priorities.items():
                    st.write(f"- {criterion}: {weight:.4f} ({weight/total*100:.2f}%)")
        
        with st.expander("🏗️ Step 3: Supermatrix Construction"):
            st.write("""
            **Unweighted Supermatrix** menghubungkan:
            - Kriteria dengan kriteria (self-loop)
            - Alternatif (jurusan) dengan kriteria
            
            Struktur supermatrix:
            ```
            [C₁ C₂ ... Cₙ | A₁ A₂ ... Aₘ]
            ────────────────────────────
            C: Kriteria RIASEC (6)
            A: Alternatif/Jurusan (n)
            ```
            
            **Weighted Supermatrix** = Unweighted × Bobot Kriteria
            """)
            
            supermatrix_size = calc_details.get('supermatrix_size', 0)
            if supermatrix_size:
                st.info(f"Dimensi Supermatrix: {supermatrix_size} × {supermatrix_size}")
        
        with st.expander("🔄 Step 4: Limit Supermatrix"):
            st.write("""
            - Mengiterasi supermatrix: W^k (k → ∞)
            - Proses konvergen ketika W^(k+1) ≈ W^k
            - Hasil: prioritas stabil untuk setiap alternatif
            """)
            
            iterations = calc_details.get('iterations', 0)
            converged = calc_details.get('converged', False)
            
            if converged:
                st.success(f"✅ Konvergen pada iterasi ke-{iterations}")
            else:
                st.warning(f"⚠️ Tidak konvergen setelah {iterations} iterasi")
        
        with st.expander("📊 Step 5: Ekstraksi Prioritas"):
            st.write("""
            - Mengambil nilai prioritas alternatif dari kolom pertama limit matrix
            - Prioritas ini = skor akhir ANP untuk setiap jurusan
            - Jurusan diurutkan dari skor tertinggi ke terendah
            """)
    
    # TAB 4: Ranking Lengkap
    with tab4:
        st.write("### 🏆 Ranking Lengkap Semua Jurusan")
        
        top_5_majors = anp_results.get('top_5_majors', [])
        
        if top_5_majors:
            # Create comprehensive ranking table
            ranking_data = []
            
            for i, major_info in enumerate(top_5_majors, 1):
                if isinstance(major_info, dict):
                    major_name = major_info.get('major_name', 'Unknown')
                    anp_score = major_info.get('anp_score', 0)
                elif isinstance(major_info, (list, tuple)) and len(major_info) >= 2:
                    major_name = major_info[0]
                    data = major_info[1]
                    anp_score = data.get('anp_score', 0)
                else:
                    continue
                
                ranking_data.append({
                    'Rank': i,
                    'Jurusan': major_name,
                    'Skor ANP': f"{anp_score:.6f}",
                    'Persentase': f"{anp_score * 100:.3f}%",
                    'Rating': "⭐" * min(5, max(1, int(anp_score * 20)))
                })
            
            ranking_df = pd.DataFrame(ranking_data)
            
            # Display with styling
            st.dataframe(
                ranking_df,
                hide_index=True,
                use_container_width=True
            )
            
            # Visualisasi skor
            majors_list = [item['Jurusan'] for item in ranking_data]
            scores_list = [float(item['Skor ANP']) for item in ranking_data]
            
            fig_ranking = go.Figure(data=[
                go.Bar(
                    x=scores_list,
                    y=majors_list,
                    orientation='h',
                    marker=dict(
                        color=scores_list,
                        colorscale='Viridis',
                        showscale=True,
                        colorbar=dict(title="Skor ANP")
                    ),
                    text=[f"{score:.4f}" for score in scores_list],
                    textposition='outside'
                )
            ])
            
            fig_ranking.update_layout(
                title="Distribusi Skor ANP",
                xaxis_title="Skor ANP",
                yaxis_title="Jurusan",
                height=max(400, len(majors_list) * 40),
                margin=dict(l=150, r=100, t=50, b=50)
            )
            
            st.plotly_chart(fig_ranking, use_container_width=True)
            
            # Detail untuk jurusan teratas
            st.markdown("---")
            st.write("### 🔍 Analisis Detail Jurusan Terbaik")
            
            if top_5_majors:
                top_major = top_5_majors[0]
                
                if isinstance(top_major, dict):
                    top_major_name = top_major.get('major_name', 'Unknown')
                    top_major_data = top_major
                elif isinstance(top_major, (list, tuple)) and len(top_major) >= 2:
                    top_major_name = top_major[0]
                    top_major_data = top_major[1]
                else:
                    top_major_name = "Unknown"
                    top_major_data = {}
                
                st.write(f"**Jurusan: {top_major_name}**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write("**Profil RIASEC Jurusan:**")
                    riasec_profile = top_major_data.get('riasec_profile', {})
                    if riasec_profile:
                        for criterion, value in riasec_profile.items():
                            st.write(f"- {criterion}: {value:.3f}")
                
                with col2:
                    st.write("**Kontribusi Kriteria:**")
                    criteria_weights = top_major_data.get('criteria_weights', {})
                    if criteria_weights:
                        sorted_contributions = sorted(
                            criteria_weights.items(), 
                            key=lambda x: x[1], 
                            reverse=True
                        )
                        for criterion, contrib in sorted_contributions:
                            st.write(f"- {criterion}: {contrib:.6f}")

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
                range=[0, max(values) * 1.1]
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
    if anp_results and anp_results.get('top_5_majors'):
        top_5_list = []
        for major_data in anp_results['top_5_majors']:
            if isinstance(major_data, dict):
                top_5_list.append(major_data.get('major_name', ''))
            elif isinstance(major_data, (list, tuple)) and len(major_data) >= 1:
                top_5_list.append(major_data[0])
        
        st.write(f"""
        Berdasarkan analisis ANP dan profil RIASEC Anda, berikut adalah saran karier:
        
        **🏆 Jurusan Utama yang Direkomendasikan:** {recommended_major}
        
        **📚 5 Pilihan Terbaik:** {', '.join(top_5_list) if top_5_list else 'Data tidak tersedia'}
        
        **💼 Bidang Karier yang Cocok:**
        - Bidang yang melibatkan karakteristik {top_3_types[0].lower()} (kekuatan utama)
        - Pekerjaan yang memadukan aspek {top_3_types[1].lower()} dan {top_3_types[2].lower()}
        - Pertimbangkan juga jurusan ranking 2-3 sebagai alternatif
        
        **🚀 Tips Pengembangan:**
        - Fokus mengembangkan keterampilan {top_3_types[0]} sebagai kekuatan utama
        - Perkuat kemampuan {top_3_types[1]} dan {top_3_types[2]} sebagai pendukung
        - Cari pengalaman magang atau proyek di bidang terkait 5 jurusan teratas
        - Pertimbangkan double major atau minor yang melengkapi profil Anda
        """)
    else:
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
        with connection_context() as conn:
            conn.execute('DELETE FROM test_results WHERE student_id = ?', (user_id,))
            conn.execute('DELETE FROM student_answers WHERE student_id = ?', (user_id,))
            conn.commit()
        st.switch_page("pages/student_test.py")

with col2:
    if st.button("🖨️ Cetak Hasil", use_container_width=True):
        st.info("Fitur cetak akan segera tersedia!")

with col3:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/student_dashboard.py")