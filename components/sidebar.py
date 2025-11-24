import streamlit as st
from utils.auth import logout

ROLE_NAV_ITEMS = {
    "admin": [
        {
            "key": "admin_dashboard",
            "label": "Dashboard Admin",
            "icon": "📊",
            "page": "pages/admin_dashboard.py",
            "description": "Statistik utama dan ringkasan aktivitas"
        },
        {
            "key": "data_management",
            "label": "Manajemen Data",
            "icon": "🗃️",
            "page": "pages/data_management.py",
            "description": "Kelola siswa, soal, dan jurusan"
        },
        {
            "key": "test_monitoring",
            "label": "Monitoring Tes",
            "icon": "📈",
            "page": "pages/test_monitoring.py",
            "description": "Pantau progres dan hasil tes"
        }
    ],
    "student": [
        {
            "key": "student_dashboard",
            "label": "Dashboard Siswa",
            "icon": "🎓",
            "page": "pages/student_dashboard.py",
            "description": "Profil dan status pengerjaan tes"
        },
        {
            "key": "student_test",
            "label": "Tes Minat Bakat",
            "icon": "📝",
            "page": "pages/student_test.py",
            "description": "Kerjakan tes RIASEC lengkap"
        },
        {
            "key": "student_results",
            "label": "Hasil Tes",
            "icon": "📊",
            "page": "pages/student_results.py",
            "description": "Lihat analisis dan rekomendasi"
        }
    ]
}

SIDEBAR_CSS = """
<style>
[data-testid="stSidebar"], [data-testid="collapsedControl"] {
    display: none !important;
}
.appview-container .main .block-container {
    padding-left: 290px;
    padding-right: 1.5rem;
    transition: padding-left 0.3s ease;
}
.custom-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: 260px;
    height: 100vh;
    padding: 1.8rem 1.2rem;
    background: linear-gradient(180deg, #0f1e3d 0%, #091028 100%);
    color: #e6edff;
    box-shadow: 6px 0 24px rgba(0, 0, 0, 0.35);
    z-index: 100;
    overflow-y: auto;
}
.custom-sidebar::-webkit-scrollbar {
    width: 4px;
}
.custom-sidebar::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 2px;
}
.custom-sidebar .sidebar-header {
    margin-bottom: 1.5rem;
}
.custom-sidebar .sidebar-brand {
    font-size: 0.85rem;
    letter-spacing: 0.2rem;
    text-transform: uppercase;
    color: #7da2ff;
}
.custom-sidebar .sidebar-user {
    font-size: 1.2rem;
    margin: 0.2rem 0 0;
}
.custom-sidebar .sidebar-role {
    font-size: 0.9rem;
    color: rgba(230, 237, 255, 0.75);
    margin: 0.2rem 0 0;
}
.custom-sidebar .nav-section-title {
    font-size: 0.8rem;
    letter-spacing: 0.1rem;
    color: rgba(125, 162, 255, 0.9);
    text-transform: uppercase;
    margin-bottom: 0.5rem;
}
.custom-sidebar .nav-btn {
    margin-bottom: 0.6rem;
}
.custom-sidebar .nav-btn button {
    background: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.15) !important;
    color: #e6edff !important;
    font-weight: 500;
    text-align: left;
    border-radius: 0.75rem !important;
}
.custom-sidebar .nav-btn.active button {
    background: linear-gradient(90deg, #5ab0ff 0%, #9ed0ff 100%) !important;
    color: #0b1423 !important;
    border-color: transparent !important;
    box-shadow: 0 10px 20px rgba(90, 176, 255, 0.25);
}
.custom-sidebar .nav-desc {
    font-size: 0.75rem;
    color: rgba(230, 237, 255, 0.7);
    margin: 0.2rem 0 0.6rem 0.2rem;
}
.custom-sidebar .sidebar-footer {
    margin-top: 2rem;
}
.custom-sidebar .sidebar-footer button {
    background: linear-gradient(270deg, #ff6b6b 0%, #ffa06b 100%) !important;
    border: none !important;
    color: #0b1423 !important;
    font-weight: 600;
}
@media (max-width: 900px) {
    .custom-sidebar {
        position: static;
        width: 100%;
        height: auto;
        border-radius: 0 0 1.5rem 1.5rem;
    }
    .appview-container .main .block-container {
        padding-left: 1.2rem;
    }
}
</style>
"""


def render_sidebar(active_page: str | None = None) -> None:
    st.markdown(SIDEBAR_CSS, unsafe_allow_html=True)

    role = st.session_state.get("role")
    full_name = st.session_state.get("full_name", "Pengguna")
    role_label = {
        "admin": "Administrator",
        "student": "Siswa"
    }.get(role, "Tamu")

    nav_items = ROLE_NAV_ITEMS.get(role, [])

    st.markdown('<div class="custom-sidebar">', unsafe_allow_html=True)

    st.markdown(
        f"""
        <div class="sidebar-header">
            <div class="sidebar-brand">Holland Portal</div>
            <p class="sidebar-role">{role_label}</p>
            <h4 class="sidebar-user">{full_name}</h4>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if nav_items:
        st.markdown('<div class="nav-section-title">Navigasi</div>', unsafe_allow_html=True)
        for item in nav_items:
            is_active = item["key"] == active_page
            st.markdown(
                f'<div class="nav-btn {"active" if is_active else ""}">',
                unsafe_allow_html=True,
            )
            if st.button(
                f"{item['icon']}  {item['label']}",
                key=f"nav_btn_{item['key']}",
                use_container_width=True,
            ):
                st.switch_page(item["page"])
            if description := item.get("description"):
                st.markdown(f'<p class="nav-desc">{description}</p>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Menu tidak tersedia untuk peran Anda.")

    st.markdown('<div class="sidebar-footer">', unsafe_allow_html=True)
    if st.button("Keluar", key="custom_sidebar_logout", use_container_width=True):
        logout()
    st.markdown('</div></div>', unsafe_allow_html=True)
  