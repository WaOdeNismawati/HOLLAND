
import streamlit as st

def show_top_navbar(role: str = "siswa"):
    """
    Renders a responsive top navigation bar based on user role using st.columns.
    """
    # Define navigation items based on role
    nav_items = {
        "admin": {
            "Dashboard": "pages/admin_dashboard.py",
            "Data Management": "pages/data_management.py",
            "Test Monitoring": "pages/test_monitoring.py",
        },
        "student": {
            "Dashboard": "pages/student_dashboard.py",
            "Tes RIASEC": "pages/student_test.py",
            "Hasil": "pages/student_results.py",
        }
    }.get(role, {})

    # Custom CSS for the navbar and buttons
    st.markdown("""
        <style>
        .stButton button {
            background-color: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 16px;
            margin: 4px 2px;
            cursor: pointer;
            border-radius: 12px;
        }
        .stButton button:hover {
            background-color: #764ba2;
        }
        </style>
    """, unsafe_allow_html=True)

    # Create a container for the navbar
    st.markdown('<hr style="margin-top: -1rem;">', unsafe_allow_html=True)

    # Use columns for layout
    cols = st.columns(len(nav_items) + 1)

    # Navigation buttons in their columns
    for i, (name, path) in enumerate(nav_items.items()):
        if cols[i].button(name, key=f"nav_{name}", use_container_width=True):
            st.switch_page(path)

    # Logout button in the last column
    if cols[-1].button("Logout", key="nav_logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")

    st.markdown('<hr style="margin-bottom: 2rem;">', unsafe_allow_html=True)
