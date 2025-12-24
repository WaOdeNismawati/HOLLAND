import streamlit as st
from streamlit_tz import streamlit_tz
from database.db_manager import DatabaseManager
from utils.auth import authenticate_user

# Konfigurasi halaman
st.set_page_config(
    page_title="Sistem Rekomendasi Jurusan",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Inisialisasi database
db_manager = DatabaseManager()
db_manager.init_database()

def main():
    # CSS to hide the hamburger menu, footer - ONLY on login page
    hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                [data-testid="stSidebarNav"] {display: none;}
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
    # Custom CSS untuk halaman login minimalist
    st.markdown("""
        <style>
        /* Background */
        .stApp {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        }
        
        /* Logo Container */
        .logo-container {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .logo-container img {
            width: 120px;
            height: 120px;
            object-fit: contain;
            margin-bottom: 1.5rem;
            filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3));
        }
        
        /* Title */
        .login-title {
            text-align: center;
            color: #ffffff;
            font-size: 2rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            text-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        
        .login-subtitle {
            text-align: center;
            color: #cbd5e0;
            font-size: 1rem;
            margin-bottom: 3rem;
        }
        
        /* Input styling */
        .stTextInput > div > div > input {
            border-radius: 10px;
            border: 2px solid rgba(255,255,255,0.2);
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            padding: 0.75rem 1rem;
            font-size: 1rem;
            color: #ffffff;
            transition: all 0.3s ease;
        }
        
        .stTextInput > div > div > input::placeholder {
            color: rgba(255,255,255,0.5);
        }
        
        .stTextInput > div > div > input:focus {
            border-color: rgba(255,255,255,0.5);
            background: rgba(255,255,255,0.15);
            box-shadow: 0 0 0 3px rgba(255, 255, 255, 0.1);
        }
        
        /* Label styling */
        .stTextInput > label {
            color: #ffffff !important;
            font-weight: 500;
        }
        
        /* Button styling */
        .stButton > button {
            width: 100%;
            background: rgba(255,255,255,0.2);
            backdrop-filter: blur(10px);
            color: white;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 10px;
            padding: 0.75rem 1.5rem;
            font-size: 1rem;
            font-weight: 600;
            transition: all 0.3s ease;
            margin-top: 1rem;
        }
        
        .stButton > button:hover {
            transform: translateY(-2px);
            background: rgba(255,255,255,0.3);
            border-color: rgba(255,255,255,0.5);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }
        
        /* Hide Streamlit elements on login page */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display: none;}
        </style>
    """, unsafe_allow_html=True)
    
    # Vertical centering
    st.markdown("<br>" * 3, unsafe_allow_html=True)
    
    # Create centered columns
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Logo
        import os
        import base64
        
        logo_html = ""
        logo_path = "assets/logo.png"
        
        if os.path.exists(logo_path):
            with open(logo_path, "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode()
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" alt="Logo">'
        
        # Logo and Title
        st.markdown(f"""
            <div class="logo-container">
                {logo_html}
            </div>
            <div class="login-title">Selamat Datang</div>
            <div class="login-subtitle">Sistem Rekomendasi Jurusan</div>
        """, unsafe_allow_html=True)
        
        # Login form (glassmorphism style)
        with st.form("login_form"):
            username = st.text_input("Nama Pengguna", placeholder="Masukkan username")
            password = st.text_input("Kata Sandi", type="password", placeholder="Masukkan password")
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
                        
                        st.success("✅ Login berhasil!")
                        st.rerun()
                    else:
                        st.error("❌ Nama pengguna atau kata sandi salah!")
                else:
                    st.error("⚠️ Mohon isi semua field!")

def redirect_to_dashboard():
    if st.session_state.role == 'admin':
        st.switch_page("pages/admin_dashboard.py")
    else:
        st.switch_page("pages/student_dashboard.py")

if __name__ == "__main__":
    main()