import streamlit as st
import base64
import os

def render_sidebar_header():
    """Renders the logo and title in the sidebar."""
    
    # Path to logo
    logo_path = "assets/logo.png"
    
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_data = base64.b64encode(f.read()).decode()
            
        st.sidebar.markdown(
            f"""
            <div style="text-align: center; margin-bottom: 2rem;">
                <img src="data:image/png;base64,{logo_data}" width="120" style="display: inline-block; margin-bottom: 1rem;">
                <p style="
                    font-weight: 600;
                    color: #e2e8f0;
                    font-size: 1.1rem;
                    line-height: 1.4;
                    margin: 0;
                ">
                    Sistem Rekomendasi<br>Jurusan Kuliah
                </p>
                <div style="
                    height: 1px;
                    background: linear-gradient(90deg, transparent, rgba(226, 232, 240, 0.2), transparent);
                    margin-top: 1.5rem;
                "></div>
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        # Fallback if logo doesn't exist
        st.sidebar.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <p style="
                    font-weight: 600;
                    color: #e2e8f0;
                    font-size: 1.1rem;
                    line-height: 1.4;
                    margin: 0;
                ">
                    Sistem Rekomendasi<br>Jurusan Kuliah
                </p>
                <div style="
                    height: 1px;
                    background: linear-gradient(90deg, transparent, rgba(226, 232, 240, 0.2), transparent);
                    margin-top: 1.5rem;
                "></div>
            </div>
            """, 
            unsafe_allow_html=True
        )
