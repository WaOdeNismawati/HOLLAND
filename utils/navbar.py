import streamlit as st
from utils.auth import logout

def show_navbar():
    """
    Displays a persistent top navigation bar based on the user's role.
    This function injects custom CSS for styling and uses st.columns
    to lay out the navigation buttons. It handles page switching and logout.
    """
    st.set_page_config(layout="wide", initial_sidebar_state="collapsed")

    # Inject custom CSS for the navbar
    st.markdown("""
        <style>
        /* Main container for the navbar */
        .navbar-container {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            background: linear-gradient(90deg, #0a2540, #1e3a8a);
            padding: 10px 2rem;
            z-index: 999;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        /* Spacer to push page content down */
        .navbar-space {
            margin-top: 80px;
        }
        </style>
    """, unsafe_allow_html=True)

    # Get user role from session state
    role = st.session_state.get("role", "student")

    # Define navigation items based on user role
    if role == "admin":
        nav_items = {
            "Dashboard": "pages/admin_dashboard.py",
            "Data Management": "pages/data_management.py",
            "Test Monitoring": "pages/test_monitoring.py",
        }
    else:
        nav_items = {
            "Dashboard": "pages/student_dashboard.py",
            "Tes RIASEC": "pages/student_test.py",
            "Hasil": "pages/student_results.py",
        }

    # Create the navbar structure using st.markdown
    st.markdown("<div class='navbar-container'>", unsafe_allow_html=True)

    # Use st.columns to lay out the navbar elements
    col1, col2 = st.columns([1, 2])

    with col1:
        st.markdown("<h2 style='color: #dbeafe; font-family: Poppins, sans-serif;'>🎓 Sistem Minat Bakat</h2>", unsafe_allow_html=True)

    with col2:
        # Use columns for the navigation links
        link_cols = st.columns(len(nav_items) + 1)
        for i, (name, page_path) in enumerate(nav_items.items()):
            if link_cols[i].button(name, key=f"nav_{name}", use_container_width=True):
                st.switch_page(page_path)

        # Logout button in the last column
        if link_cols[-1].button("Logout", key="nav_logout", use_container_width=True):
            logout()

    st.markdown("</div>", unsafe_allow_html=True)

    # Add a spacer to prevent content from being hidden behind the navbar
    st.markdown("<div class='navbar-space'></div>", unsafe_allow_html=True)