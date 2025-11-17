from collections.abc import Callable, Sequence

import streamlit as st

from src.core.auth import logout

DEFAULT_ADMIN_MENU = (
    ("🏠 Dashboard Admin", "pages/admin_dashboard.py"),
    ("🗃️ Manajemen Data", "pages/data_management.py"),
    ("📊 Monitoring Tes", "pages/test_monitoring.py"),
)

DEFAULT_STUDENT_MENU = (
    ("🏠 Dashboard", "pages/student_dashboard.py"),
    ("📝 Tes Minat Bakat", "pages/student_test.py"),
    ("📊 Hasil Tes", "pages/student_results.py"),
)


def render_sidebar(
    *,
    role: str | None = None,
    title: str | None = None,
    menu_items: Sequence[tuple[str, str]] | None = None,
    extra_content: Callable[[], None] | None = None,
    show_logout: bool = True,
):
    """Render sidebar generik untuk admin maupun siswa."""

    current_role = role or st.session_state.get('role')
    if not current_role:
        return

    if current_role == 'admin':
        header = title or "🗃️ Portal Admin"
        menu = menu_items or DEFAULT_ADMIN_MENU
        greeting = f"Admin: {st.session_state.get('full_name', '')}"
        logout_label = "Logout"
    else:
        header = title or "🎓 Portal Siswa"
        menu = menu_items or DEFAULT_STUDENT_MENU
        greeting = f"Selamat datang, {st.session_state.get('full_name', '')}"
        logout_label = "Keluar"

    with st.sidebar:
        st.title(header)
        if greeting.strip():
            st.write(greeting)

        st.markdown("---")

        for label, page in menu:
            if st.button(label, use_container_width=True):
                st.switch_page(page)

        if extra_content:
            st.markdown("---")
            extra_content()

        if show_logout:
            st.markdown("---")
            if st.button(logout_label, type="primary", use_container_width=True):
                logout()


# Backward compatibility alias
sidebar = render_sidebar