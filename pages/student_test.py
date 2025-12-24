import math
import time

import streamlit as st

from utils.auth import check_login
from utils.holland_calculator import HollandCalculator
from utils.config import connection
from services.cat_engine import CATHollandEngine
from database.db_manager import DatabaseManager
from components.sidebar import render_sidebar
from utils.styles import apply_dark_theme

st.set_page_config(page_title="Tes Minat Bakat", page_icon="📝", layout="wide", initial_sidebar_state="expanded")

# Apply dark theme
apply_dark_theme()

# Cek login
check_login()

# Render sidebar
st.session_state.current_page = 'student_test'
render_sidebar()


ANSWER_LABELS = {
    1: "1 - Sangat Tidak Setuju",
    2: "2 - Tidak Setuju",
    3: "3 - Netral",
    4: "4 - Setuju",
    5: "5 - Sangat Setuju"
}


def _persist_answers(session_state):
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (session_state['student_id'],))
    for entry in session_state['answers']:
        cursor.execute('''
            INSERT INTO student_answers (student_id, question_id, answer, question_order, response_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            session_state['student_id'],
            entry['question_id'],
            entry['answer'],
            entry['question_order'],
            entry['response_time']
        ))
    conn.commit()
    conn.close()


def _reset_cat_session(engine: CATHollandEngine):
    st.session_state['cat_test_session'] = engine.initialize_session(st.session_state.user_id)
    st.session_state['cat_test_session']['question_start'] = time.time()


def _finalize_test():
    session_state = st.session_state['cat_test_session']
    if not session_state['answers']:
        st.warning("Belum ada jawaban yang disimpan.")
        return

    _persist_answers(session_state)
    calculator = HollandCalculator()
    # Proses hasil tes
    result = calculator.process_test_completion(
        session_state['student_id'],
        total_items=len(session_state['answers'])
    )
    session_state['result'] = result
    session_state['finished'] = True
    st.success("🎉 Tes berhasil diselesaikan!")


def _handle_answer_submission(engine: CATHollandEngine, question_id: int, answer_value: int):
    session_state = st.session_state['cat_test_session']
    question = engine.get_question(question_id)
    if not question:
        st.error("Soal tidak tersedia.")
        return

    response_time = max(0.1, time.time() - (session_state.get('question_start') or time.time()))
    order = len(session_state['answers']) + 1
    session_state['answers'].append({
        'question_id': question_id,
        'answer': answer_value,
        'question_order': order,
        'response_time': response_time
    })
    session_state['asked_ids'].append(question_id)

    # Pilih soal berikutnya dengan urutan yang bervariasi (hindari tipe beruntun)
    next_question = engine.select_next_question(session_state['theta'], session_state['asked_ids'])
    if next_question:
        session_state['current_question_id'] = next_question['id']
        session_state['question_start'] = time.time()
    else:
        session_state['completed'] = True

    # Cek apakah sudah selesai (semua soal dijawab)
    if engine.should_stop(len(session_state['answers']), None):
        session_state['completed'] = True

    st.rerun()


# ==============================
#  Halaman Tes
# ==============================
check_login()
st.set_page_config(page_title="Tes Minat Bakat", page_icon="📝", layout="wide", initial_sidebar_state="collapsed")

conn = connection()

if st.session_state.role != 'student':
    st.error("Akses ditolak! Halaman ini hanya untuk siswa.")
    st.stop()

cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM test_results WHERE student_id = ?', (st.session_state.user_id,))
if cursor.fetchone()[0] > 0:
    st.warning("⚠️ Anda sudah menyelesaikan tes ini.")
    st.info("Jika Anda ingin mengambil tes kembali, silakan hubungi administrator untuk mereset hasil Anda.")
    if st.button("Lihat Hasil Tes"):
        st.switch_page("pages/student_results.py")
    st.stop()

conn.close()

# Initialize CAT Engine untuk tes minat bakat
# max_items=None: semua soal harus dijawab untuk hasil akurat
# CAT digunakan untuk mengacak urutan soal agar tidak beruntun tipe yang sama
engine = CATHollandEngine(min_items=18, max_items=None, target_se=0.35)
if not engine.question_bank:
    st.error("Tidak ada soal yang tersedia. Hubungi administrator.")
    st.stop()

if 'cat_test_session' not in st.session_state or \
        st.session_state['cat_test_session'].get('student_id') != st.session_state.user_id:
    _reset_cat_session(engine)

session_state = st.session_state['cat_test_session']
if session_state['question_start'] is None and session_state['current_question_id']:
    session_state['question_start'] = time.time()

progress = len(session_state['answers'])
total_questions = session_state['max_questions']
st.progress(min(1.0, progress / total_questions))

st.markdown(f"""
### 📝 Progress Tes Minat Bakat
**{progress} dari {total_questions} soal terjawab** ({(progress/total_questions*100):.1f}%)
""")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("📊 Soal Terjawab", f"{progress}/{total_questions}")
with col2:
    remaining = total_questions - progress
    st.metric("⏳ Soal Tersisa", f"{remaining}")
with col3:
    if st.button("🔄 Ulangi Tes", use_container_width=True):
        _reset_cat_session(engine)
        st.rerun()

st.markdown("---")

if not session_state['completed'] and session_state['current_question_id']:
    question = engine.get_question(session_state['current_question_id'])
    
    # Holland type icons
    holland_icons = {
        'Realistic': '🔧',
        'Investigative': '🔬',
        'Artistic': '🎨',
        'Social': '👥',
        'Enterprising': '💼',
        'Conventional': '📊'
    }
    
    icon = holland_icons.get(question['holland_type'], '📌')
    
    st.markdown(f"""
    ### {icon} Soal {progress + 1} dari {total_questions}
    **Kategori: {question['holland_type']}**
    """)
    
    st.info(question['question_text'])

    with st.form("cat_question_form"):
        answer_value = st.radio(
            "Pilih jawaban:",
            options=list(ANSWER_LABELS.keys()),
            format_func=lambda x: ANSWER_LABELS[x],
            index=2,
            horizontal=True,
            key=f"answer_{question['id']}_{progress}"
        )
        submitted = st.form_submit_button("Jawab & Lanjut", type="primary")

    if submitted:
        _handle_answer_submission(engine, question['id'], int(answer_value))
else:
    st.info("Tes adaptif selesai. Simpan hasil untuk melihat rekomendasi.")
    if session_state.get('result') is None:
        if st.button("🚀 Selesaikan Tes & Proses Hasil", type="primary", use_container_width=True):
            with st.spinner("Memproses hasil tes..."):
                _finalize_test()
            st.rerun()

if session_state.get('result'):
    result = session_state['result']
    st.success("Hasil tes tersedia")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Holland Code")
        st.info(result['holland_code'])
        st.write("**3 Tipe Teratas:**")
        for i, holland_type in enumerate(result['top_3_types'], 1):
            score = result['scores'][holland_type]
            st.write(f"{i}. {holland_type} ({score:.3f})")

    with col2:
        st.subheader("Rekomendasi Jurusan")
        if result.get('recommended_major'):
            st.success(f"🎓 {result['recommended_major']}")
        else:
            st.warning("Rekomendasi tidak tersedia")

        if result.get('anp_results') and result['anp_results'].get('top_5_majors'):
            st.write("Alternatif lainnya:")
            for i, major_data in enumerate(result['anp_results']['top_5_majors'][:3], 1):
                if isinstance(major_data, dict):
                    st.write(f"{i}. {major_data.get('major_name', 'Unknown')} (Score: {major_data.get('anp_score', 0):.4f})")
                elif isinstance(major_data, (list, tuple)) and len(major_data) >= 2:
                    st.write(f"{i}. {major_data[0]} (Score: {major_data[1].get('anp_score', 0):.4f})")

    st.markdown("---")
    if st.button("📄 Lihat Hasil Lengkap", type="primary", use_container_width=True):
        st.switch_page("pages/student_results.py")