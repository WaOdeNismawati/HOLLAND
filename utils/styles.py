"""
Modul styling untuk tema dark minimalist dan navigasi berbasis role.
"""
import streamlit as st
from components.sidebar import render_sidebar_header


def apply_theme():
    """Apply light theme with navy blue accents CSS to Streamlit pages."""
    theme_css = """
    <style>
        /* === DARK NAVY THEME (REFERENCE STYLE) === */
        :root {
            --bg-primary: #0f172a; /* Deep Navy Blue (Main Background) */
            --bg-secondary: #1e293b; /* Slate Blue (Sidebar) */
            --bg-card: #ffffff;
            --accent-primary: #3b82f6; /* Bright Blue (Primary Actions) */
            --accent-secondary: #2563eb; /* Darker Blue (Hover) */
            --accent-brand: #0f172a; /* Matching Navy for brand header */
            
            --text-primary: #f1f5f9; /* Light text on dark background */
            --text-secondary: #94a3b8; /* Dimmed text on dark background */
            --text-on-card: #1e293b; /* Dark text inside white cards */
            --text-on-sidebar: #e2e8f0; /* White-ish text on sidebar */
            
            --border-color: #334155; /* Borders suitable for dark theme */
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
        }
        
        /* Hide Streamlit default elements */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Hide default Streamlit sidebar navigation */
        [data-testid="stSidebarNav"] {display: none;}
        
        /* Main background */
        .stApp {
            background: var(--bg-primary);
        }
        
        /* Main container padding */
        .main .block-container {
            padding-top: 4.5rem;
            max-width: 95%;
        }
        
        /* GLOBAL TEXT STYLING FOR DARK THEME */
        :root {
            --text-primary: #ffffff !important; /* Pure White as requested */
            --text-secondary: #cbd5e1 !important; /* Light Slate for secondary */
        }
        
        /* Enforce white text on all headers and standard text containers */
        h1, h2, h3, h4, h5, h6, 
        .stMarkdown p, .stMarkdown span, .stMarkdown li,
        [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] span,
        [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 {
            color: #ffffff !important;
        }

        /* Specifically target Streamlit headers which might be wrapped */
        .stHeadingContainer h1, .stHeadingContainer h2, .stHeadingContainer h3, 
        .stHeadingContainer h4, .stHeadingContainer h5, .stHeadingContainer h6 {
            color: #ffffff !important;
        }
        
        /* Ensure specific headers are white (Streamlit sometimes wraps them weirdly) */
        [data-testid="stHeader"] {
            background-color: transparent;
        }
        
        /* Widget styling to ensure contrast */
        .stSelectbox label, .stTextInput label, .stNumberInput label, .stTextArea label, .stRadio label {
            color: #ffffff !important;
            font-weight: 500;
        }

        /* INPUT TEXT COLOR - Force Black for readability inside white boxes */
        .stTextInput input, .stNumberInput input, .stTextArea textarea, 
        .stSelectbox div[data-baseweb="select"] div {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            caret-color: #000000;
        }
        
        /* Expander Title Styling */
        .streamlit-expanderHeader p, [data-testid="stExpander"] summary p {
            color: #ffffff !important;
            font-weight: 600;
        }
        
        /* Specific overrides for card content need to be dark */
        .card h1, .card h2, .card h3, .card h4, .card h5, .card h6, 
        .card p, .card li, .card span, .card div, .card label {
            color: var(--text-on-card) !important;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background: var(--bg-secondary);
            border-right: 1px solid var(--border-color);
        }
        
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
            color: var(--text-on-sidebar) !important;
            font-size: 0.95rem;
        }

        /* Brand Header in Sidebar */
        .brand-header {
            background: rgba(0,0,0,0.2);
            height: 3.125rem;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 1.25rem;
            font-weight: 500;
            font-style: italic;
            margin-top: -4rem;
            margin-bottom: 0;
            width: 100%;
        }

        /* Top Navbar Area - Transparent/Dark Blend */
        [data-testid="stHeader"] {
            background-color: transparent !important;
            border-bottom: none;
            z-index: 1000;
            height: 3.125rem;
        }

        /* Integrated Navbar Header Styling */
        .navbar-header {
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            height: 3.125rem;
            background: rgba(15, 23, 42, 0.95); /* Semi-transparent Navy */
            backdrop-filter: blur(10px);
            z-index: 1001;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 20px;
            pointer-events: none;
            border-bottom: 1px solid var(--border-color);
        }

        /* GLOBAL FORM STYLING - TRANSPARENT CARD EFFECT */
        [data-testid="stForm"] {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 24px;
            padding: 2.5rem 2rem;
            border: 1px solid rgba(255, 255, 255, 0.2);
            box-shadow: 
                0 25px 50px -12px rgba(0, 0, 0, 0.25), 
                0 0 100px -20px rgba(59, 130, 246, 0.3);
            text-align: center;
            margin-bottom: 2rem;
        }

        /* Adjust padding for forms inside expanders or smaller containers if needed */
        [data-testid="stExpander"] [data-testid="stForm"] {
            padding: 1.5rem;
            box-shadow: none; /* Less shadow for nested forms */
            background: rgba(255, 255, 255, 0.95); /* Slightly more opaque for nested */
        }

        /* Text colors inside StMarkdown (Global) */
        .stMarkdown p, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6, .stMarkdown li {
            color: var(--text-primary) !important;
        }

        /* Card-like containers (stMetric) & Custom Cards */
        [data-testid="metric-container"], .card, [data-testid="stForm"] {
            background: var(--bg-card);
            padding: 1.5rem;
            border-radius: 12px;
            border: none;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        }
        
        /* FORCE Text color inside cards to be DARK */
        [data-testid="metric-container"] p, 
        .card p, .card h1, .card h2, .card h3, .card span,
        [data-testid="stForm"] p, [data-testid="stForm"] label {
            color: var(--text-on-card) !important;
        }

        /* Sidebar User Profile */
        .sidebar-user {
            padding: 15px;
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }
        .sidebar-user-img {
            width: 45px;
            height: 45px;
            border-radius: 50%;
            margin-right: 15px;
            border: 2px solid var(--accent-primary);
        }
        .sidebar-user-info {
            display: flex;
            flex-direction: column;
        }
        .sidebar-user-name {
            color: white !important;
            font-weight: 600;
            font-size: 0.85rem;
            margin: 0;
        }
        .sidebar-status {
            color: #94a3b8 !important;
            font-size: 0.75rem;
            margin-top: 5px;
            display: flex;
            align-items: center;
        }
        .status-dot {
            height: 8px;
            width: 8px;
            background-color: #10b981;
            border-radius: 50%;
            display: inline-block;
            margin-right: 5px;
            box-shadow: 0 0 5px #10b981;
        }
        
        /* Navbar User Info */
        .navbar-user-info {
            color: white;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            display: flex;
            align-items: center;
            pointer-events: auto;
        }

        /* Sidebar Menu Items */
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
            background: transparent !important;
            color: #cbd5e1 !important;
            border: none !important;
            border-radius: 8px !important;
            text-align: left !important;
            justify-content: flex-start !important;
            font-size: 0.9rem !important;
            padding: 10px 15px !important;
            width: 100% !important;
            display: flex !important;
            align-items: center !important;
            height: auto !important;
            margin-bottom: 5px !important;
        }
        
        /* Hover State */
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"]:hover {
            background: rgba(255,255,255,0.05) !important;
            color: white !important;
        }

        /* Menu Separators */
        hr {
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 1.5rem 0;
        }

        /* BUTTON STYLING - Match 'Browse Files' (Outline Style) */
        .stButton > button, 
        [data-testid="stFormSubmitButton"] > button {
            background-color: transparent !important;
            border: 1px solid rgba(255, 255, 255, 0.4) !important;
            color: #ffffff !important;
            border-radius: 8px !important;
            padding: 0.5rem 1rem !important;
            font-weight: 500 !important;
            transition: all 0.2s ease !important;
        }

        .stButton > button:hover, 
        [data-testid="stFormSubmitButton"] > button:hover {
            background-color: rgba(255, 255, 255, 0.1) !important;
            border-color: #ffffff !important;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1) !important;
            transform: translateY(-1px);
        }

        .stButton > button:active, 
        [data-testid="stFormSubmitButton"] > button:active {
            background-color: rgba(255, 255, 255, 0.2) !important;
            transform: translateY(0);
        }
        
        /* Input fields */
        .stTextInput > div > div > input,
        .stSelectbox > div > div,
        .stTextArea > div > div > textarea {
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            color: var(--text-primary);
        }
        
        /* Tabs */
        .stTabs [data-baseweb="tab-list"] {
            background: #f1f5f9;
            border-radius: 8px;
            padding: 4px;
        }
        
        /* Tabs - Aggressive Override */
        .stTabs [data-baseweb="tab"],
        .stTabs [data-baseweb="tab"] p,
        .stTabs [data-baseweb="tab"] div,
        .stTabs [data-baseweb="tab"] span {
            color: #000000 !important;
            -webkit-text-fill-color: #000000 !important;
            font-weight: 600 !important;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 6px;
            background-color: transparent;
        }
        
        .stTabs [aria-selected="true"] {
            background: white;
            color: var(--accent-primary);
            box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        }
        
        /* Expanders */
        .streamlit-expanderHeader {
            background: var(--bg-card);
            border-radius: 8px;
            border: 1px solid var(--border-color);
        }
        
        /* Metrics */
        [data-testid="stMetricValue"] {
            color: var(--accent-primary) !important;
            font-size: 2rem;
            font-weight: 700;
        }
        
        /* Custom classes */
        .card {
            background: var(--bg-card);
            border-radius: 12px;
            padding: 1.5rem;
            border: 1px solid var(--border-color);
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            margin-bottom: 1rem;
        }
        
        .nav-button:hover {
            background: #f1f5f9;
            color: var(--accent-primary);
        }
        
        .nav-button.active {
            background: var(--accent-primary);
            color: white;
        }
        
        /* Divider */
        hr {
            border: none;
            border-top: 1px solid var(--border-color);
            margin: 1.5rem 0;
        }

        /* Form styling */
        [data-testid="stForm"] {
            background: var(--bg-card);
            padding: 1.5rem;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        }
    </style>
    """
    st.markdown(theme_css, unsafe_allow_html=True)


def apply_dark_theme():
    """Alias for compatibility while transitioning to theme name."""
    apply_theme()


def render_sidebar(current_page: str = ""):
    """Render sidebar navigation bergaya CAT."""
    with st.sidebar:
        # Sidebar Header Branding
        render_sidebar_header()
        
        # User details from session state
        full_name = st.session_state.get('full_name', 'Guest')
        role_label = 'ADMINISTRATOR' if st.session_state.get('role') == 'admin' else 'STUDENT'
        
        # Sidebar User Profile
        st.markdown(f"""
        <div class="sidebar-user">
            <img src="https://www.w3schools.com/howto/img_avatar.png" class="sidebar-user-img">
            <div class="sidebar-user-info">
                <p class="sidebar-user-name">{full_name.upper()}</p>
                <div class="sidebar-status">
                    <span class="status-dot"></span> Online
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Navigation based on role
        role = st.session_state.get('role', 'student')
        
        st.markdown('<p style="padding-left: 15px; text-transform: uppercase; font-size: 0.7rem; color: #4b646f; font-weight: 700;">MAIN NAVIGATION</p>', unsafe_allow_html=True)
        
        if role == 'admin':
            _render_admin_menu(current_page)
        else:
            _render_student_menu(current_page)
        
        # Logout button styled like a menu item
        if st.button("🚪 LOGOUT", key="logout_btn", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.switch_page("app.py")


def _render_admin_menu(current_page: str):
    """Render menu navigasi admin bergaya CAT."""
    menu_items = [
        ("📂 Dashboard", "admin_dashboard", "pages/admin_dashboard.py"),
        ("📝 Monitoring Tes", "test_monitoring", "pages/test_monitoring.py"),
        ("⚙️ Manajemen Data", "data_management", "pages/data_management.py"),
    ]
    
    for label, page_id, page_path in menu_items:
        is_active = current_page == page_id
        active_class = "active" if is_active else ""
        if st.button(
            label, 
            key=f"nav_{page_id}",
            use_container_width=True,
            help=label
        ):
            st.switch_page(page_path)


def _render_student_menu(current_page: str):
    """Render menu navigasi siswa bergaya CAT."""
    menu_items = [
        ("🏠 Dashboard", "student_dashboard", "pages/student_dashboard.py"),
        ("✏️ Mulai Tes", "student_test", "pages/student_test.py"),
        ("📊 Hasil Tes", "student_results", "pages/student_results.py"),
    ]
    
    for label, page_id, page_path in menu_items:
        is_active = current_page == page_id
        if st.button(
            label, 
            key=f"nav_{page_id}",
            use_container_width=True
        ):
            st.switch_page(page_path)


def page_header(title: str, subtitle: str = ""):
    """Render header halaman bergaya CAT (Title + Subtitle breadcrumb style)."""
    full_name = st.session_state.get('full_name', 'Administrator')
    
    # Render Top Navbar User Info
    st.markdown(f"""
    <div class="navbar-header">
        <div class="navbar-user-info">
            <span style="margin-right: 10px;">👤 {full_name.upper()}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render Content Header
    st.markdown(f"""
    <div style="display: flex; align-items: baseline; margin-bottom: 20px;">
        <h1 style="color: #f1f5f9; margin: 0; font-size: 1.5rem; font-weight: 400;">{title}</h1>
        <small style="color: #94a3b8; margin-left: 10px; font-size: 0.9rem;">{subtitle}</small>
    </div>
    """, unsafe_allow_html=True)


def metric_card(label: str, value: str, icon: str = "", delta: str = ""):
    """Render metric card dengan styling dark theme."""
    delta_html = ""
    if delta:
        color = "#10b981" if delta.startswith("+") else "#ef4444"
        delta_html = f'<p style="color: {color}; font-size: 0.875rem; margin: 0;">{delta}</p>'
    
    st.markdown(f"""
    <div style="background: #ffffff; padding: 1.25rem; border-radius: 12px; border: 1px solid #e2e8f0; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <p style="color: #64748b; font-size: 0.875rem; margin: 0;">{icon} {label}</p>
        <p style="color: #1e3a8a; font-size: 2rem; font-weight: 700; margin: 0.5rem 0 0 0;">{value}</p>
        {delta_html}
    </div>
    """, unsafe_allow_html=True)
