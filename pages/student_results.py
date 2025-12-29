import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.auth import check_login
from utils.timezone import convert_utc_to_local
from utils.config import connection

# Cek login & koneksi database
check_login()
conn = connection()

if st.session_state.role != 'student':
    st.error("Akses ditolak! Halaman ini hanya untuk siswa.")
    st.stop()

st.set_page_config(page_title="Hasil Tes", page_icon="📊", layout="wide")

# Main content
st.title("📊 Hasil Tes Minat Bakat Anda")
st.markdown("---")

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
top_3_types = json.loads(result[2])
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

# Get rankings from nested structure  
major_rankings = anp_results.get('major_rankings', [])
if not major_rankings and 'anp_results' in anp_results:
    nested_rankings = anp_results.get('anp_results', {}).get('ranked_majors', [])
    major_rankings = [[item[0], item[1]['hybrid_score']] for item in nested_rankings if len(item) >= 2]

# Get calculation details
calc_details = anp_results.get('anp_results', {}) if 'anp_results' in anp_results else anp_results

# Extract consistency_ratio, is_consistent and converged status
consistency_ratio = None
is_consistent = False
converged = True

# Priority extraction: Try nested structure first (common case)
if 'anp_results' in anp_results and isinstance(anp_results.get('anp_results'), dict):
    nested = anp_results['anp_results']
    
    # Extract from calculation_details (primary location)
    if 'calculation_details' in nested and isinstance(nested['calculation_details'], dict):
        calc_details_nested = nested['calculation_details']
        consistency_ratio = calc_details_nested.get('consistency_ratio')
        is_consistent = calc_details_nested.get('is_consistent', False)
        converged = calc_details_nested.get('converged', True)
    
    # Fallback: Try top level of nested (secondary location)
    if consistency_ratio is None:
        consistency_ratio = nested.get('consistency_ratio')
        is_consistent = nested.get('is_consistent', False)
        converged = nested.get('converged', True)

# Last resort: Direct access from calc_details
if consistency_ratio is None:
    consistency_ratio = calc_details.get('consistency_ratio')
    is_consistent = calc_details.get('is_consistent', False)
    converged = calc_details.get('converged', True)

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
                len(major_rankings) if major_rankings else 0,
                help="Total jurusan yang dianalisis ANP"
            )
        
        with col2:
            cr_value = calc_details.get('consistency_ratio', 0)
            is_consistent = calc_details.get('is_consistent', False)
            st.metric(
                "Consistency Ratio",
                f"{consistency_ratio:.4f}" if consistency_ratio is not None else "N/A",
                "✓ Konsisten" if is_consistent else "✓ Valid" if (consistency_ratio is not None and consistency_ratio < 0.1) else "⚠ Review",
                help="CR < 0.1 dianggap konsisten"
            )
        
        with col3:
            st.metric(
                "Metode",
                "Hybrid ANP",
                help="ANP + Weighted Score + Cosine Similarity"
            )
        
        with col4:
            st.metric(
                "Status",
                "✓ Konvergen" if converged else "⚠ Check",
                help="Status konvergensi supermatrix"
            )
        
        st.markdown("---")
        
        # Penjelasan metodologi
        st.success("""
        **🎯 HYBRID WEIGHTED SCORING**
        
        Sistem ini menggabungkan kekuatan dari tiga metode:
        
        1. **ANP (Analytic Network Process)** untuk menghitung bobot kriteria RIASEC
           - Skor RIASEC Anda dinormalisasi ke skala 0-1
           - Dibuat **pairwise comparison matrix** dengan ratio antar skor
           - Ratio otomatis di-clip ke skala Saaty (1/9 hingga 9)
           - Menghitung priority vector menggunakan eigenvalue method
        
        2. **Weighted Scoring** untuk menghitung kesesuaian dengan jurusan
           - Formula: Σ(bobot_kriteria_ANP × profil_jurusan × skor_siswa)
        
        3. **Cosine Similarity** untuk mengukur kemiripan pola profil
           - Nilai 0-1 (semakin mendekati 1 = semakin mirip)
        
        4. **Hybrid Score** = 60% Weighted Score + 40% Cosine Similarity
        
        **Keunggulan:** Akurasi tinggi, diferensiasi jelas, dan performa cepat!
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
        methodology = anp_results.get('methodology', 'ANP')
        
        if major_rankings:
            st.info(f"📌 Menampilkan Top {min(len(major_rankings), 20)} dari {len(major_rankings)} jurusan")
            
            # Top 20
            top_20 = major_rankings[:20]
            df_majors = pd.DataFrame(top_20, columns=['Jurusan', 'Hybrid Score'])
            df_majors.index = range(1, len(df_majors) + 1)
            df_majors['Hybrid Score'] = df_majors['Hybrid Score'].round(4)
            
            # Display with styling
            st.dataframe(
                df_majors.style.background_gradient(subset=['Hybrid Score'], cmap='Greens'),
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
                title="Top 10 Jurusan (Hybrid Score)",
                xaxis_title="Hybrid Score",
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
col1, col2 = st.columns(2)

with col1:
    if st.button("🖨️ Cetak Hasil", use_container_width=True):
        st.info("Fitur cetak akan segera tersedia!")

with col2:
    if st.button("🏠 Dashboard", use_container_width=True):
        st.switch_page("pages/student_dashboard.py")