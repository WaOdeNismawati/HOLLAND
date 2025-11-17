import sys
from pathlib import Path

import bcrypt
import sqlite3
import time
import streamlit as st
from streamlit_tz import streamlit_tz

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from src.core.auth import authenticate_user, hash_password
from src.infrastructure.database.db_manager import DatabaseManager

# Konfigurasi halaman
st.set_page_config(
    page_title="Sistem Tes Minat Bakat",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inisialisasi database
db_manager = DatabaseManager()
db_manager.init_database()

def main():
    # Cek status login
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.last_active = None
    
    if not st.session_state.logged_in:
        show_login_page()
    else:
        redirect_to_dashboard()

def show_login_page():
    st.title("🎓 Sistem Tes Minat Bakat Siswa")
    st.markdown("---")

    logout_message = st.session_state.pop('logout_message', None)
    if logout_message:
        st.info(logout_message)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.subheader("Masuk ke Sistem")
        
        with st.form("login_form"):
            username = st.text_input("Nama Pengguna")
            password = st.text_input("Kata Sandi", type="password")
            submit_button = st.form_submit_button("Masuk")
            
            if submit_button:
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
                        # Get timezone from browser
                        browser_timezone = streamlit_tz()

                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.role = user[3]
                        st.session_state.full_name = user[4]
                        st.session_state.class_name = user[5] if user[5] else ""
                        st.session_state.timezone = browser_timezone if browser_timezone else 'Asia/Jakarta'
                        st.session_state.last_active = time.time()
                        
                        st.success("Login berhasil!")
                        st.rerun()
                    else:
                        st.error("Nama pengguna atau kata sandi salah!")
                else:
                    st.error("Mohon isi semua field!")

def redirect_to_dashboard():
    if st.session_state.role == 'admin':
        st.switch_page("pages/admin_dashboard.py")
    else:
        st.switch_page("pages/student_dashboard.py")

if __name__ == "__main__":
    main()