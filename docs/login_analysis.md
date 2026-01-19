
# Analisis Proses Login Sistem HOLLAND

Berikut adalah analisis teknis dari alur login pada sistem Anda, berdasarkan pemeriksaan kode pada `app.py` dan `utils/auth.py`.

## 1. Deskripsi Alur (Narrative Detail)

Sequence diagram login ini menggambarkan interaksi teknis yang presisi antar komponen sistem dalam memproses autentikasi pengguna. Proses diinisialisasi oleh **Streamlit UI** sebagai antarmuka utama yang menampilkan form login dan menangkap input *username* serta *password* dari pengguna. Setelah tombol "Masuk" ditekan, Streamlit UI mengirimkan kredensial tersebut ke **Auth System** (modul `utils/auth.py`), yang bertindak sebagai jembatan logika keamanan.

**Auth System** kemudian meminta data pengguna ke **Database (SQLite)** melalui query `SELECT` spesifik berdasarkan username. **Database** merespons dengan mengembalikan record pengguna yang relevan, termasuk hash password yang tersimpan. Setelah data diterima, **Auth System** melakukan verifikasi kriptografis menggunakan *bcrypt* untuk mencocokkan password input dengan hash dari database.

Jika verifikasi valid, **Auth System** mengembalikan objek user lengkap ke **Streamlit UI**. Sebagai langkah final, **Streamlit UI** memperbarui *Session State* untuk menyimpan status login, dan secara otomatis melakukan *reroute* (pengalihan) pengguna ke halaman dashboard yang sesuai dengan role mereka (Admin atau Siswa), menyelesaikan siklus login.

---

## 2. Alur Proses (Detail Langkah)

1.  **Inisialisasi**:
    - Aplikasi (`app.py`) berjalan.
    - Sistem memeriksa `st.session_state.logged_in`. Jika belum ada, di-set ke `False`.
    - Jika user belum login, fungsi `show_login_page()` dipanggil.

2.  **Interaksi User (UI)**:
    - Form login ditampilkan dengan field **Username** dan **Password**.
    - User mengisi data dan menekan tombol "**MASUK SEKARANG**".

3.  **Halaman Depan (Frontend Logic)**:
    - Input ditangkap dari session state (`u_input`, `p_input`).
    - Validasi dasar: Memastikan field tidak kosong.

4.  **Autentikasi (Backend Logic)**:
    - Fungsi `authenticate_user(username, password)` di `utils/auth.py` dipanggil.
    - **Koneksi Database**: `DatabaseManager` membuka koneksi ke SQLite.
    - **Query**: `SELECT ... FROM users WHERE username = ?`.
    - **Verifikasi Password**: Menggunakan `bcrypt.checkpw` untuk membandingkan password input dengan hash yang tersimpan.
    - **Hasil**: Mengembalikan tuple data user jika cocok, atau `None` jika gagal.

5.  **Penanganan Hasil**:
    - **Jika Berhasil**:
        - Session state diupdate dengan data user (`user_id`, `role`, `full_name`, dll).
        - Pesan sukses ditampilkan.
        - `st.rerun()` dipicu untuk me-refresh aplikasi.
        - Pada run berikutnya, pengecekan login bernilai `True`.
        - Fungsi `redirect_to_dashboard()` dipanggil.
            - Jika role `admin` -> redirect ke `pages/admin_dashboard.py`.
            - Jika role `student` -> redirect ke `pages/student_dashboard.py`.
    - **Jika Gagal**:
        - Menampilkan pesan error "Username atau password salah!".

---

## 3. Prompt Sequence Diagram (Format Khusus)

Gunakan prompt ini untuk membuat diagram dengan style yang Anda inginkan (cocok untuk sequencediagram.org).

**Prompt:**

```text
Buatkan Sequence Diagram untuk alur Login aplikasi saya dengan syntax khusus berikut.

**Syntax Guidelines:**
- Gunakan `bottomparticipants`
- Gunakan icon `materialdesignicons` (e141 untuk UI, e371 untuk Auth, e325 untuk DB)
- `actor User`

**Alur:**
1. User ke UI: Masukkan Username/Password & Submit.
2. UI ke Auth: Panggil fungsi authenticate_user.
3. Auth ke DB: Query SELECT user by username.
4. DB ke Auth: Return User Data (Hash Pwd).
5. Auth self: Cek password (bcrypt).
6. Auth ke UI: Return hasil validasi.
7. UI self: Set Session & Redirect.

**Output Code:**
Berikan kode diagramnya saja dalam blok code.
```

---

## 4. Hasil Diagram (Syntax Sequencediagram.org)

Berikut adalah kode diagram yang disesuaikan dengan contoh style yang Anda berikan.

```text
bottomparticipants

actor User
materialdesignicons e141 "Streamlit\nUI" as UI
materialdesignicons e371 "Auth\nSystem" as Auth
materialdesignicons e325 "SQLite\nDB" as DB

User->UI:Buka Aplikasi
UI->UI:Cek Session (logged_in=False)
UI->User:Tampilkan Form Login

User->UI:Input Creds & "Masuk Sekarang"
UI->UI:Validasi Input Not Empty

alt Input Valid
    UI->Auth:authenticate_user(u, p)
    Auth->DB:SELECT * FROM users
    DB->Auth:Return User Row (Hash)
    
    Auth->Auth:bcrypt.checkpw()
    
    alt Password OK
        Auth->UI:Return User Info
        UI->UI:Set Session State & Rerun
        UI->User:Tampilkan "Login Berhasil"
        UI->UI:redirect_to_dashboard()
    else Password Salah
        Auth->UI:Return None
        UI->User:Error "Username/Pass Salah"
    end
else Input Kosong
    UI->User:Warning "Isi semua field"
end
```
