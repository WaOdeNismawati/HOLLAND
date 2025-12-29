sequenceDiagram
    participant User as 👤 User (Browser)
    participant UI as 🖥️ Streamlit UI<br/>(app.py)
    participant Auth as 🔐 Auth Module<br/>(utils/auth.py)
    participant DB as 🗄️ DatabaseManager<br/>(db_manager.py)
    participant SQLite as 💾 SQLite Database<br/>(exam_system.db)

    User->>UI: Buka halaman login
    UI->>UI: Cek st.session_state.logged_in
    alt Belum login
        UI->>UI: show_login_page()
        UI-->>User: Tampilkan form login
    end

    User->>UI: Input username & password
    User->>UI: Klik tombol "Masuk"
    
    UI->>UI: Validasi input tidak kosong
    alt Input kosong
        UI-->>User: ⚠️ "Mohon isi semua field!"
    end

    UI->>Auth: authenticate_user(username, password)
    Auth->>DB: DatabaseManager()
    DB->>SQLite: sqlite3.connect()
    SQLite-->>DB: Connection object
    DB-->>Auth: db_manager instance
    
    Auth->>DB: get_connection()
    DB-->>Auth: conn (SQLite connection)
    
    Auth->>SQLite: SELECT id, username, password,<br/>role, full_name, class_name<br/>FROM users WHERE username = ?
    SQLite-->>Auth: user record (atau None)
    Auth->>Auth: conn.close()

    alt User ditemukan
        Auth->>Auth: bcrypt.checkpw(password, stored_password)
        alt Password valid
            Auth-->>UI: Return user tuple<br/>(id, username, password, role, full_name, class_name)
            UI->>UI: Set session_state:<br/>• logged_in = True<br/>• user_id, username, role<br/>• full_name, class_name, timezone
            UI-->>User: ✅ "Login berhasil!"
            UI->>UI: st.rerun()
            UI->>UI: redirect_to_dashboard()
            alt Role = admin
                UI->>User: Redirect ke admin_dashboard.py
            else Role = student
                UI->>User: Redirect ke student_dashboard.py
            end
        else Password tidak valid
            Auth-->>UI: Return None
            UI-->>User: ❌ "Nama pengguna atau kata sandi salah!"
        end
    else User tidak ditemukan
        Auth-->>UI: Return None
        UI-->>User: ❌ "Nama pengguna atau kata sandi salah!"
    end