import streamlit as st
import sqlite3
import bcrypt
from streamlit_tz import streamlit_tz
from database.db_manager import DatabaseManager
from utils.auth import authenticate_user, hash_password

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
    # CSS to hide the hamburger menu and footer
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
    st.markdown(hide_streamlit_style, unsafe_allow_html=True)

    # Cek status login
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        show_login_page()
    else:
        redirect_to_dashboard()

def show_login_page():
    st.title("🎓 Sistem Tes Minat Bakat Siswa")
    st.markdown("---")
    
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
                        timezone = streamlit_tz()

                        st.session_state.logged_in = True
                        st.session_state.user_id = user[0]
                        st.session_state.username = user[1]
                        st.session_state.role = user[3]
                        st.session_state.full_name = user[4]
                        st.session_state.class_name = user[5] if user[5] else ""
                        st.session_state.timezone = timezone if timezone else 'Asia/Jakarta'
                        
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