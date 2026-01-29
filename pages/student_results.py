import streamlit as st
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from utils.auth import check_login
from utils.timezone import convert_utc_to_local
from utils.config import connection
from utils.styles import apply_dark_theme, render_sidebar, page_header

# Page config
st.set_page_config(page_title="Hasil Tes", page_icon="📊", layout="wide")
apply_dark_theme()

# Check login & connection
check_login()
conn = connection()

if st.session_state.role != 'student':
    st.error("Akses ditolak! Halaman ini hanya untuk siswa.")
    st.stop()

# Sidebar
render_sidebar(current_page="student_results")

# Page header
page_header("Hasil Tes Minat Bakat", "Analisis profil RIASEC dan rekomendasi jurusan Anda")

cursor = conn.cursor()

# Ambil hasil tes siswa
cursor.execute('''
    SELECT holland_scores, anp_results, top_3_types, recommended_major, completed_at
    FROM test_results 
    WHERE student_id = ?
''', (st.session_state.user_id,))

result = cursor.fetchone()

# Fetch all student answers joined with questions
cursor.execute('''
    SELECT q.id, q.question_text, q.holland_type, sa.answer, sa.response_time
    FROM questions q
    LEFT JOIN student_answers sa ON q.id = sa.question_id AND sa.student_id = ?
    ORDER BY q.id
''', (st.session_state.user_id,))
student_answers_data = cursor.fetchall()
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
    major_rankings = [[item[0], item[1].get('hybrid_score', item[1].get('anp_score', 0))] for item in nested_rankings if len(item) >= 2]

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
        <div class="card" style="text-align: center;">
            <div style="font-size: 2em;">{desc['icon']}</div>
            <h4 style="margin: 10px 0 5px 0; color: #1e3a8a;">#{i+1} {desc['title']}</h4>
            <p style="font-size: 0.9em; color: #475569; margin: 5px 0;">{desc['desc']}</p>
            <div style="background-color: #1e3a8a; color: white; padding: 5px; border-radius: 5px; margin-top: 10px;">
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
    tab1, tab2, tab3 = st.tabs([
        "📊 Ringkasan Hasil", 
        "📝 Detail Jawaban",
        "🏆 Ranking Lengkap"
    ])
    
    # TAB 1: Ringkasan Hasil
    with tab1:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Jurusan Dianalisis",
                len(major_rankings) if major_rankings else 0,
                help="Total jurusan yang dianalisis ANP"
            )
        
        with col2:
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
        
        st.markdown("---")

    # TAB 2: Detail Jawaban
    with tab2:
        st.write("### 📝 Detail Jawaban")
        st.markdown("Berikut adalah rincian jawaban Anda untuk ke-60 soal tes minat bakat.")

        if not student_answers_data:
            st.warning("⚠️ Data jawaban tidak ditemukan.")
        else:
            # Map answers to labels
            answer_labels = {
                1: "1 - Sangat Tidak Setuju",
                2: "2 - Tidak Setuju",
                3: "3 - Netral",
                4: "4 - Setuju",
                5: "5 - Sangat Setuju"
            }
            
            # Prepare data for dataframe
            answers_list = []
            for row in student_answers_data:
                q_id, q_text, q_type, q_ans, q_time = row
                answers_list.append({
                    "No": q_id,
                    "Pertanyaan": q_text,
                    "Tipe RIASEC": q_type,
                    "Jawaban": answer_labels.get(q_ans, "Belum dijawab") if q_ans else "Belum dijawab",
                    "Waktu (detik)": f"{q_time:.2f}" if q_time is not None else "0.00"
                })
            
            df_answers = pd.DataFrame(answers_list)
            
            # Display stats
            col_a, col_b, col_c = st.columns([1, 1, 2])
            with col_a:
                st.metric("Total Soal", len(df_answers))
            with col_b:
                answered_count = sum(1 for row in student_answers_data if row[3] is not None)
                st.metric("Terjawab", answered_count)
            
            st.markdown("---")

            # Display table with styling
            st.dataframe(
                df_answers,
                column_config={
                    "No": st.column_config.NumberColumn("No", width="small"),
                    "Pertanyaan": st.column_config.TextColumn("Pertanyaan", width="large"),
                    "Tipe RIASEC": st.column_config.TextColumn("Tipe RIASEC", width="medium"),
                    "Jawaban": st.column_config.TextColumn("Jawaban", width="medium"),
                    "Waktu (detik)": st.column_config.TextColumn("Waktu (detik)", width="small"),
                },
                hide_index=True,
                use_container_width=True
            )
    
    # TAB 3``: Ranking Lengkap
    with tab3:
        st.write("### 🏆 Ranking Lengkap Semua Jurusan")
        
        top_5_majors = anp_results.get('top_5_majors', [])
        methodology = anp_results.get('methodology', 'ANP')
        
        if major_rankings:
            st.info(f"📌 Menampilkan Top {min(len(major_rankings), 20)} dari {len(major_rankings)} jurusan")
            
            # Top 20
            top_20 = major_rankings[:20]
            df_majors = pd.DataFrame(top_20, columns=['Jurusan', 'ANP Score'])
            df_majors.index = range(1, len(df_majors) + 1)
            df_majors['ANP Score'] = df_majors['ANP Score'].round(4)
            
            # Display with styling
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
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font_color='#f1f5f9',
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