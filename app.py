import streamlit as st
from streamlit_tz import streamlit_tz
from database.db_manager import DatabaseManager
from utils.auth import authenticate_user
from utils.styles import apply_dark_theme

# Konfigurasi halaman
st.set_page_config(
    page_title="HOLLAND - Sistem Rekomendasi Jurusan Kuliah",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply dark theme
apply_dark_theme()

# Inisialisasi database
db_manager = DatabaseManager()
db_manager.init_database()


def main():
    # Cek status login
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        show_login_page()
    else:
        redirect_to_dashboard()


def show_login_page():
    # Centered login container with High-Fidelity CSS
    st.markdown("""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        * {
            font-family: 'Inter', sans-serif !important;
        }
        
        .stApp {
            background-color: #020617; /* Slate 950 */
            background-image: 
                radial-gradient(circle at 15% 50%, rgba(59, 130, 246, 0.15) 0%, transparent 25%), 
                radial-gradient(circle at 85% 30%, rgba(14, 165, 233, 0.15) 0%, transparent 25%);
            background-size: 100% 100%;
        }
        
        /* Grid overlay pattern */
        .stApp::before {
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
            background-size: 40px 40px;
            pointer-events: none;
            z-index: 0;
        }

        /* CARD STYLING - Target the FORM itself */
        [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 24px;
            padding: 5rem 2rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 
                0 25px 50px -12px rgba(0, 0, 0, 0.25), 
                0 0 100px -20px rgba(59, 130, 246, 0.3);
            text-align: center;
        }
        .login-title {
            color: #0f172a;
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 0.5rem;
            letter-spacing: -0.025em;
        }
        
        .login-subtitle {
            color: #64748b;
            font-size: 0.95rem;
            margin-bottom: 2rem;
            font-weight: 500;
        }
        
        /* Input styling */
        .stTextInput > div {
            border-radius: 12px !important;
        }
        
        .stTextInput > div > div {
            background-color: #f8fafc;
            border-radius: 12px;
            border: 1px solid #e2e8f0;
            transition: all 0.2s;
        }
        
        .stTextInput > div > div > input {
            color: #0f172a;
            padding: 0.875rem 1rem;
            font-size: 1rem;
            background-color: transparent;
        }
        
        .stTextInput > div > div:focus-within {
            border-color: #3b82f6;
            box-shadow: 0 0 0 4px rgba(59, 130, 246, 0.1);
            background-color: #ffffff;
        }

        /* Button Styling */
        .stButton > button {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
            color: white;
            border: none;
            border-radius: 12px;
            padding: 0.875rem 1rem;
            font-weight: 600;
            font-size: 1rem;
            width: 100%;
            margin-top: 0.5rem;
            box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.3);
            transition: all 0.2s;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 15px -3px rgba(37, 99, 235, 0.4);
        }
        
        .stButton > button:active {
            transform: translateY(0);
        }

        /* Hide Streamlit elements */
        [data-testid="stSidebar"], [data-testid="stSidebarNav"], [data-testid="collapsedControl"] {
            display: none !important;
        }
        .stMain {
            margin: 0;
            padding: 0;
        }
        header {
            visibility: hidden;
        }
        
        /* Ensure centering */
        [data-testid="stHorizontalBlock"] {
            align-items: center;
        }
        
        /* Fix footer spacing */
        .login-footer {
            text-align: center; 
            margin-top: 1.5rem; 
            color: #94a3b8; 
            font-size: 0.8rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    # Load Logo
    import base64
    try:
        with open("assets/logo.png", "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
            logo_html = f'<img src="data:image/png;base64,{logo_data}" width="100" style="display: block;">'
    except FileNotFoundError:
        logo_html = '<div style="font-size: 3rem;">🎓</div>'

    # Layout: Use 3 columns, middle one IS THE FORM CONTAINER
    col1, col2, col3 = st.columns([1, 1.2, 1])
    
    with col2:
        # EVERYTHING inside the form to ensure unified card styling
        with st.form("login_form"):
            # 1. Header (Logo + Text)
            st.markdown(f"""
                <div style="display: flex; justify-content: center;">
                    <div class="logo-container">
                        {logo_html}
                    </div>
                </div>
                <div style="text-align: center;">
                    <div class="login-title">Selamat Datang</div>
                    <div class="login-subtitle">Sistem Rekomendasi Jurusan Kuliah</div>
                </div>
            """, unsafe_allow_html=True)
            
            # 2. Inputs in the same container
            st.text_input("Username", placeholder="Masukkan Username", label_visibility="collapsed", key="u_input")
            st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True) # Small spacer
            st.text_input("Password", type="password", placeholder="Masukkan Password", label_visibility="collapsed", key="p_input")
            
            # 3. Submit Button
            st.markdown('<div style="height: 20px;"></div>', unsafe_allow_html=True) # Spacer
            submit_button = st.form_submit_button("MASUK SEKARANG", use_container_width=True)
            
            # 4. Footer
            st.markdown("""
                <div class="login-footer">
                    SMA Negeri 1 Ladongi
                </div>
            """, unsafe_allow_html=True)
            
            if submit_button:
                username = st.session_state.u_input
                password = st.session_state.p_input
                
                if username and password:
                    user = authenticate_user(username, password)
                    if user:
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
                        st.error("Username atau password salah!")
                else:
                    st.warning("Mohon isi semua field!")


def redirect_to_dashboard():
    if st.session_state.role == 'admin':
        st.switch_page("pages/admin_dashboard.py")
    else:
        st.switch_page("pages/student_dashboard.py")


if __name__ == "__main__":
    main()