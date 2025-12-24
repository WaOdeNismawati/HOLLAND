import streamlit as st
from utils.auth import logout
from database.db_manager import DatabaseManager # Diperlukan untuk fungsi student_navigation

@st.cache_data(ttl=60)
def check_test_completion(user_id):
    """Cache test completion status for 60 seconds"""
    db = DatabaseManager()
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM test_results WHERE student_id = ?', (user_id,))
    count = cursor.fetchone()[0]
    conn.close()
    return count > 0

def render_sidebar():
    """
    Render sidebar navigation based on user role, 
    designed to visually mimic the uploaded dashboard image.
    Call this function at the top of every page.
    """
    # =======================================================
    # CUSTOM CSS: Meniru tampilan sidebar seperti di gambar
    # =======================================================
    st.markdown("""
        <style>
        /* FORCE SHOW SIDEBAR - Override any hidden state */
        [data-testid="stSidebar"] {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            width: 250px !important;
            min-width: 250px !important;
            max-width: 250px !important;
            transform: translateX(0) !important;
            transition: none !important;
            background-color: #343a40; /* Warna gelap ala dashboard */
            color: #ffffff;
            padding: 0 !important;
            margin: 0 !important;
            position: fixed;
            height: 100vh;
            overflow-y: auto;
            top: 0 !important;
            left: 0 !important;
            z-index: 999 !important;
        }
        
        /* Force show the sidebar content */
        [data-testid="stSidebar"] > div {
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }
        
        /* Hilangkan padding di content sidebar */
        [data-testid="stSidebar"] > div:first-child {
            padding-top: 0 !important;
            margin-top: 0 !important;
        }
        
        /* Hilangkan space di block element streamlit */
        [data-testid="stSidebar"] .element-container:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Hilangkan vertical space di markdown */
        [data-testid="stSidebar"] .stMarkdown:first-child {
            margin-top: 0 !important;
            padding-top: 0 !important;
        }
        
        /* Scrollbar styling untuk sidebar */
        [data-testid="stSidebar"]::-webkit-scrollbar {
            width: 8px;
        }
        
        [data-testid="stSidebar"]::-webkit-scrollbar-track {
            background: #212529;
        }
        
        [data-testid="stSidebar"]::-webkit-scrollbar-thumb {
            background: #495057;
            border-radius: 4px;
        }
        
        [data-testid="stSidebar"]::-webkit-scrollbar-thumb:hover {
            background: #6c757d;
        }
        
        /* Menghilangkan navigasi default Streamlit (jika ada) */
        [data-testid="stSidebarNav"] {
            display: none;
        }
        
        /* Hide menu Deploy, Settings, Rerun, etc */
        #MainMenu {
            visibility: hidden;
        }
        
        /* Hide Streamlit header */
        header {
            visibility: hidden;
        }
        
        /* Hide footer "Made with Streamlit" */
        footer {
            visibility: hidden;
        }
        
        /* SHOW hamburger menu di sidebar - untuk toggle */
        [data-testid="collapsedControl"] {
            display: block !important;
            visibility: visible !important;
        }
        
        /* Adjust main content to make space for sidebar */
        .main .block-container {
            padding-left: 270px;
        }
        
        /* FIXED HEADER CONTAINER - Logo + Text */
        .sidebar-fixed-header {
            position: sticky;
            top: 0;
            z-index: 999;
            background-color: #212529;
            padding: 1rem;
            margin: 0 !important;
            display: flex;
            align-items: center;
            gap: 0.75rem;
            border-bottom: 1px solid #495057;
        }
        
        /* LOGO STYLING - Small and inline */
        .sidebar-logo {
            width: 50px;
            height: 50px;
            object-fit: contain;
            border-radius: 8px;
            flex-shrink: 0;
        }
        
        /* HEADER TEXT */
        .sidebar-header-text {
            color: #ffffff;
            font-weight: bold;
            font-size: 1rem;
            line-height: 1.2;
            flex-grow: 1;
        }

        .profile-section-custom {
            padding: 0.5rem 1rem 0.5rem 1rem;
            margin-bottom: 1rem;
            background-color: #343a40; /* Warna latar belakang sidebar */
        }
        
        .profile-section-custom p {
            margin: 0;
            color: #ffffff;
            font-size: 0.9rem;
        }
        
        /* CUSTOM BUTTON STYLING: Meniru menu sidebar bawaan */
        .stButton button {
            width: 100%;
            text-align: left;
            padding: 0.75rem 1rem;
            margin: 0;
            border: none;
            border-radius: 0; /* Tidak ada sudut melengkung */
            background-color: transparent;
            cursor: pointer;
            transition: background-color 0.2s;
            color: #ffffff; /* Teks putih untuk sidebar gelap */
            font-size: 1rem;
        }
        
        /* Hover state */
        .stButton button:hover {
            background-color: #495057; /* Warna hover sedikit lebih terang */
            color: #ffffff;
        }
        
        /* Active state (Menu yang sedang aktif) */
        /* Karena Streamlit tidak memiliki state "active" bawaan untuk button, 
           kita gunakan warna primary untuk simulasi */
        .stButton button[data-testid="stColor-primary"] {
            background-color: #007bff; /* Biru terang untuk menandai aktif */
            color: #ffffff;
            font-weight: bold;
        }
        
        /* Logout Button Styling */
        .logout-container .stButton button {
            background-color: #dc3545 !important;
            color: white !important;
            border-radius: 0.5rem;
            margin-top: 1rem;
            padding: 0.5rem 1rem;
        }
        .logout-container .stButton button:hover {
            background-color: #c82333 !important;
        }
        
        /* Padding antar group menu */
        .menu-group-title {
            color: #adb5bd; /* Abu-abu untuk judul grup */
            padding: 1rem 1rem 0.5rem 1rem;
            font-size: 0.85rem;
            text-transform: uppercase;
        }
        
        </style>
    """, unsafe_allow_html=True)
    
    with st.sidebar:
        # FIXED HEADER: Logo + Text (Side by Side)
        import os
        import base64
        
        logo_path = "assets/logo.png"
        logo_html = ""
        
        if os.path.exists(logo_path):
            # Encode logo to base64 untuk embed di HTML
            with open(logo_path, "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode()
            logo_html = f'<img src="data:image/png;base64,{logo_base64}" class="sidebar-logo" alt="Logo">'
        
        # Render fixed header dengan logo dan text
        st.markdown(f'''
            <div class="sidebar-fixed-header">
                {logo_html}
                <div class="sidebar-header-text">Sistem Rekomendasi<br>Jurusan</div>
            </div>
        ''', unsafe_allow_html=True)
        
        # PROFILE SECTION
        if st.session_state.get('logged_in', False):
            st.markdown('<div class="profile-section-custom">', unsafe_allow_html=True)
            
            # Icon dan Nama Pengguna
            st.markdown(f'<p>🧑 **{st.session_state.full_name}**</p>', unsafe_allow_html=True)
            
            # Status / Role
            if st.session_state.role == 'student':
                class_name = st.session_state.get('class_name', 'Tidak ada kelas')
                st.markdown(f'<p style="color:#28a745;"> Online | Siswa Kelas: {class_name}</p>', unsafe_allow_html=True)
            else:
                st.markdown('<p style="color:#28a745;"> Online | Administrator</p>', unsafe_allow_html=True)
                
            st.markdown('</div>', unsafe_allow_html=True)
        
        # NAVIGATION MENU
        if st.session_state.get('role') == 'admin':
            render_admin_navigation()
        elif st.session_state.get('role') == 'student':
            render_student_navigation()
        
        # LOGOUT BUTTON
        st.markdown('<div class="logout-container">', unsafe_allow_html=True)
        if st.button("🚪 Logout", type="secondary", use_container_width=True):
            logout()
        st.markdown('</div>', unsafe_allow_html=True)


def render_admin_navigation():
    """Render navigation menu for admin"""
    st.markdown('<div class="menu-group-title">Menu Utama</div>', unsafe_allow_html=True)
    
    # Get current page
    current_page = st.session_state.get('current_page', 'admin_dashboard')
    
    # Dashboard
    if st.button("📊 Dashboard", 
                 key="nav_dashboard",
                 use_container_width=True,
                 # Gunakan type="primary" untuk simulasi 'active' state dengan warna biru
                 type="primary" if current_page == 'admin_dashboard' else "secondary"):
        st.session_state.current_page = 'admin_dashboard'
        st.switch_page("pages/admin_dashboard.py")

    
    # Data Management
    if st.button("🗃️ Manajemen Data", 
                 key="nav_data",
                 use_container_width=True,
                 type="primary" if current_page == 'data_management' else "secondary"):
        st.session_state.current_page = 'data_management'
        st.switch_page("pages/data_management.py")
    
    # Test Monitoring
    if st.button("📈 Monitoring Tes", 
                 key="nav_monitoring",
                 use_container_width=True,
                 type="primary" if current_page == 'test_monitoring' else "secondary"):
        st.session_state.current_page = 'test_monitoring'
        st.switch_page("pages/test_monitoring.py")
    

def render_student_navigation():
    """Render navigation menu for student"""
    st.markdown('<div class="menu-group-title">Menu Utama</div>', unsafe_allow_html=True)
    
    # Get current page
    current_page = st.session_state.get('current_page', 'student_dashboard')
    
    # Dashboard
    if st.button("🏠 Dashboard", 
                 key="nav_dashboard",
                 use_container_width=True,
                 type="primary" if current_page == 'student_dashboard' else "secondary"):
        st.session_state.current_page = 'student_dashboard'
        st.switch_page("pages/student_dashboard.py")
    
    # Check if student has completed test (with caching)
    test_completed = check_test_completion(st.session_state.user_id)
    
    # Test or Results button based on completion status
    if test_completed:
        if st.button("📊 Hasil Tes", 
                     key="nav_results",
                     use_container_width=True,
                     type="primary" if current_page == 'student_results' else "secondary"):
            st.session_state.current_page = 'student_results'
            st.switch_page("pages/student_results.py")
    else:
        if st.button("📝 Mulai Tes", 
                     key="nav_test",
                     use_container_width=True,
                     type="primary" if current_page == 'student_test' else "secondary"):
            st.session_state.current_page = 'student_test'
            st.switch_page("pages/student_test.py")

