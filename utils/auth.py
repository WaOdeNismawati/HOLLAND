import sqlite3
import bcrypt
from database.db_manager import DatabaseManager

def authenticate_user(username, password):
    """Autentikasi user berdasarkan username dan password"""
    db_manager = DatabaseManager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, username, password, role, full_name, class_name
        FROM users WHERE username = ?
    ''', (username,))
    
    user = cursor.fetchone()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user[2]):
        return user
    return None

def hash_password(password):
    """Hash password menggunakan bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

def check_login():
    """Cek apakah user sudah login"""
    import streamlit as st
    if 'logged_in' not in st.session_state or not st.session_state.logged_in:
        st.error("Anda harus login terlebih dahulu!")
        st.switch_page("app.py")
        st.stop()

def logout():
    """Logout user"""
    import streamlit as st
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.switch_page("app.py")