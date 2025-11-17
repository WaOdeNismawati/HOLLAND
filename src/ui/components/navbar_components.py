from pathlib import Path

import streamlit as st

from src.core.auth import logout

PROJECT_ROOT = Path(__file__).resolve().parents[3]
STATIC_DIR = PROJECT_ROOT / "static"

def load_css():
    """Load the global CSS file"""
    css_file = STATIC_DIR / "css" / "global_style.css"
    
    if css_file.exists():
        with open(css_file) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        # Fallback inline CSS if file not found
        st.markdown("""
        <style>
        .top-navbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem 2rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin: -1rem -1rem 2rem -1rem;
        }
        .brand {
            color: white;
            font-size: 1.5rem;
            font-weight: bold;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        .nav-links {
            display: flex;
            gap: 1rem;
            align-items: center;
        }
        .nav-links a {
            color: white;
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 5px;
            transition: all 0.3s;
            font-weight: 500;
        }
        .nav-links a:hover {
            background: rgba(255,255,255,0.2);
            transform: translateY(-2px);
        }
        .nav-links a.active {
            background: rgba(255,255,255,0.3);
            font-weight: bold;
        }
        .logout-btn {
            background-color: #ff4757;
            color: white;
            border: none;
            padding: 0.5rem 1.5rem;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s;
        }
        .logout-btn:hover {
            background-color: #ff3838;
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        }
        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        [data-testid="stSidebarNav"] {display: none;}
        section[data-testid="stSidebar"] {display: none;}
        
        /* Style Streamlit buttons to look like navbar buttons */
        .stButton button {
            background-color: transparent !important;
            color: white !important;
            border: none !important;
            padding: 0.5rem 1rem !important;
            border-radius: 5px !important;
            transition: all 0.3s !important;
            font-weight: 500 !important;
        }
        .stButton button:hover {
            background: rgba(255,255,255,0.2) !important;
            transform: translateY(-2px) !important;
        }
        </style>
        """, unsafe_allow_html=True)

def show_top_navbar(role: str = "siswa"):
    """
    Navbar horizontal elegan dengan CSS styling
    """
    
    # Load CSS
    load_css()
    
    # Get current page from session state
    current_page = st.session_state.get("current_page", "dashboard")
    
    # Build navigation items based on role
    if role == "admin":
        nav_items = [
            ("Dashboard", "admin_dashboard", "pages/admin_dashboard.py"),
            ("Data Management", "data_management", "pages/data_management.py"),
            ("Test Monitoring", "test_monitoring", "pages/test_monitoring.py"),
            ("Student Test", "student_test", "pages/student_test.py"),
        ]
    else:  # siswa
        nav_items = [
            ("Dashboard", "student_dashboard", "pages/student_dashboard.py"),
            ("Tes RIASEC", "student_test", "pages/student_test.py"),
            ("Hasil", "student_results", "pages/student_results.py"),
        ]
    
    # Create navbar HTML structure
    st.markdown('<div class="top-navbar">', unsafe_allow_html=True)
    
    # Brand and navigation
    cols = st.columns([2] + [1] * (len(nav_items) + 1))
    
    with cols[0]:
        st.markdown('<div class="brand">Sistem Minat Bakat</div>', unsafe_allow_html=True)
    
    # Navigation buttons
    for idx, (name, page_id, page_path) in enumerate(nav_items):
        with cols[idx + 1]:
            if st.button(name, key=f"nav_{page_id}", use_container_width=True):
                st.session_state.current_page = page_id
                st.switch_page(page_path)
    
    # Logout button
    with cols[-1]:
        if st.button("Logout", key="nav_logout", use_container_width=True):
            logout()
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Add some spacing after navbar
    st.markdown("<br>", unsafe_allow_html=True)