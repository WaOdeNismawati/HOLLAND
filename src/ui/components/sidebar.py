import streamlit as st

from src.core.auth import logout

def sidebar():
  if st.session_state.role == "admin":
    with st.sidebar:
      st.title("🗃️ Manajemen Data")
      st.write(f"Admin: {st.session_state.full_name}")
      
    if st.button("🏠 Dashboard Admin"):
        st.switch_page("pages/admin_dashboard.py")
  
  if st.session_state.role == "student":      
    with st.sidebar:
      st.title("🎓 Portal Siswa")
      st.write(f"Selamat datang, {st.session_state.full_name}")
    
      st.markdown("---")
    
      # Navigation
      st.subheader("Menu")
      if st.button("📝 Tes Minat Bakat", use_container_width=True):
        st.switch_page("pages/student_test.py")
    
      if st.button("📊 Hasil Tes", use_container_width=True):
        st.switch_page("pages/student_results.py")
    
      st.markdown("---")
    
      if st.button("Keluar", type="primary"):
        logout()
    
    
  