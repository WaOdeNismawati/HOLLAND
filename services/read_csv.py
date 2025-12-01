import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, timezone
from database.db_manager import DatabaseManager

WITA = timezone(timedelta(hours=8))

def save_csv_to_db_student(file_csv: str):
    try:
        if not file_csv:
            raise ValueError("File CSV tidak ditemukan.")
        
        # Load CSV
        df = pd.read_csv(file_csv)

        # Pilih hanya kolom yang kamu butuhkan (abaikan kolom lebih)
        required_columns = ["username", "password", "full_name", "class_name"]

        df = df[required_columns]

        # Tambahkan kolom default
        df["role"] = "student"
        df["created_at"] = datetime.now(WITA)

        conn = DatabaseManager().get_connection()
        df.to_sql("users", conn, if_exists="append", index=False)
        conn.close()
        
        print("✅ Data berhasil dimasukkan ke database.")
        return "✅ Data berhasil dimasukkan ke database."

    except Exception as e:
        return f"❌ Error: {e}"

def save_csv_to_db_soal(file_csv: str):
    try:
        if not file_csv:
            raise ValueError("File CSV tidak ditemukan.")
        
        # Load CSV
        df = pd.read_csv(file_csv)

        # Pastikan hanya kolom yang dibutuhkan
        df = df[["question_text", "holland_type"]]

        # Mapping singkatan ke nama lengkap
        mapping = {
            "R": "Realistic",
            "I": "Investigative",
            "A": "Artistic",
            "S": "Social",
            "E": "Enterprising",
            "C": "Conventional"
        }
        df["holland_type"] = df["holland_type"].map(mapping)

        # Tambahkan kolom created_at manual (WITA)
        df["created_at"] = datetime.now(WITA)

        # Simpan ke database
        conn = DatabaseManager().get_connection()
        df.to_sql("questions", conn, if_exists="append", index=False)
        conn.close()

        print("✅ Data soal RIASEC berhasil dimasukkan ke database.")
        return "✅ Data soal RIASEC berhasil dimasukkan ke database."

    except Exception as e:
        return f"❌ Error: {e}"

def save_csv_to_db_majors(file_csv: str):
    try:
        if not file_csv:
            raise ValueError("File CSV tidak ditemukan.")
        
        # Load CSV
        df = pd.read_csv(file_csv)

        # Pastikan hanya kolom yang dibutuhkan
        required_columns = ["Major", "Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"]
        df = df[required_columns]

        # Simpan ke database
        conn = DatabaseManager().get_connection()
        df.to_sql("majors", conn, if_exists="append", index=False)
        conn.close()

        print("✅ Data jurusan berhasil dimasukkan ke database.")
        return "✅ Data jurusan berhasil dimasukkan ke database."

    except Exception as e:
        return f"❌ Error: {e}"


def save_csv_to_db_student_answers(uploaded_file):
    """
    Simpan data jawaban siswa dari CSV ke database
    
    Format CSV yang diharapkan:
    - student_id, question_id, answer
    atau
    - username, question_id, answer (akan di-convert ke student_id)
    """
    try:
        # Baca file CSV/Excel
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        else:  # Excel (.xls, .xlsx)
            df = pd.read_excel(uploaded_file)
        
        # Validasi kolom yang diperlukan
        required_columns_option1 = ['student_id', 'question_id', 'answer']
        required_columns_option2 = ['username', 'question_id', 'answer']
        
        if all(col in df.columns for col in required_columns_option1):
            use_student_id = True
        elif all(col in df.columns for col in required_columns_option2):
            use_student_id = False
        else:
            st.error(f"❌ Format CSV tidak valid!")
            st.info(f"**Kolom yang diperlukan:** {required_columns_option1} ATAU {required_columns_option2}")
            st.info(f"**Kolom yang ditemukan:** {list(df.columns)}")
            return
        
        # Koneksi database
        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()
        
        # Jika menggunakan username, convert ke student_id
        if not use_student_id:
            st.info("🔄 Mengkonversi username ke student_id...")
            
            # Buat mapping username -> student_id
            cursor.execute("SELECT id, username FROM users WHERE role = 'student'")
            username_map = {row[1]: row[0] for row in cursor.fetchall()}
            
            # Tambahkan kolom student_id
            df['student_id'] = df['username'].map(username_map)
            
            # Check username yang tidak ditemukan
            missing_usernames = df[df['student_id'].isna()]['username'].unique()
            if len(missing_usernames) > 0:
                st.warning(f"⚠️ Username tidak ditemukan: {', '.join(map(str, missing_usernames))}")
                df = df.dropna(subset=['student_id'])
        
        # Validasi dan konversi tipe data
        df['student_id'] = df['student_id'].astype(int)
        df['question_id'] = df['question_id'].astype(int)
        df['answer'] = df['answer'].astype(int)
        
        # Validasi rentang jawaban (1-5)
        invalid_answers = df[(df['answer'] < 1) | (df['answer'] > 5)]
        if len(invalid_answers) > 0:
            st.warning(f"⚠️ Ditemukan {len(invalid_answers)} jawaban di luar rentang 1-5. Data ini diabaikan.")
            df = df[(df['answer'] >= 1) & (df['answer'] <= 5)]
        
        # Validasi student_id exists
        cursor.execute("SELECT id FROM users WHERE role = 'student'")
        valid_student_ids = [row[0] for row in cursor.fetchall()]
        invalid_students = df[~df['student_id'].isin(valid_student_ids)]
        if len(invalid_students) > 0:
            st.warning(f"⚠️ Ditemukan {len(invalid_students)} data dengan student_id tidak valid. Data ini diabaikan.")
            df = df[df['student_id'].isin(valid_student_ids)]
        
        # Validasi question_id exists
        cursor.execute("SELECT id FROM questions")
        valid_question_ids = [row[0] for row in cursor.fetchall()]
        invalid_questions = df[~df['question_id'].isin(valid_question_ids)]
        if len(invalid_questions) > 0:
            st.warning(f"⚠️ Ditemukan {len(invalid_questions)} data dengan question_id tidak valid. Data ini diabaikan.")
            df = df[df['question_id'].isin(valid_question_ids)]
        
        if len(df) == 0:
            st.error("❌ Tidak ada data valid untuk disimpan.")
            conn.close()
            return
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Insert data dengan handling duplicate
        success_count = 0
        update_count = 0
        error_count = 0
        
        total_rows = len(df)
        
        for idx, row in df.iterrows():
            try:
                # Check apakah data sudah ada
                cursor.execute('''
                    SELECT id FROM student_answers 
                    WHERE student_id = ? AND question_id = ?
                ''', (int(row['student_id']), int(row['question_id'])))
                
                existing = cursor.fetchone()
                
                if existing:
                    # Update jika sudah ada
                    cursor.execute('''
                        UPDATE student_answers 
                        SET answer = ? 
                        WHERE student_id = ? AND question_id = ?
                    ''', (int(row['answer']), int(row['student_id']), int(row['question_id'])))
                    update_count += 1
                else:
                    # Insert jika belum ada
                    cursor.execute('''
                        INSERT INTO student_answers (student_id, question_id, answer)
                        VALUES (?, ?, ?)
                    ''', (int(row['student_id']), int(row['question_id']), int(row['answer'])))
                    success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"Error pada baris {idx}: {e}")
            
            # Update progress
            progress = (idx + 1) / total_rows
            progress_bar.progress(progress)
            status_text.text(f"Memproses: {idx + 1}/{total_rows} baris...")
        
        conn.commit()
        conn.close()
        
        # Clear progress
        progress_bar.empty()
        status_text.empty()
        
        # Tampilkan hasil
        st.success(f"✅ Data berhasil diproses!")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("📥 Data Baru", success_count)
        with col2:
            st.metric("🔄 Data Diupdate", update_count)
        with col3:
            st.metric("❌ Error", error_count)
        
        # Tampilkan summary
        with st.expander("📊 Detail Upload"):
            st.write(f"**Total baris diproses:** {total_rows}")
            st.write(f"**Siswa unik:** {df['student_id'].nunique()}")
            st.write(f"**Soal dijawab:** {df['question_id'].nunique()}")
            
            # Preview 5 baris pertama
            st.write("**Preview 5 baris pertama:**")
            display_df = df[['student_id', 'question_id', 'answer']].head()
            st.dataframe(display_df, use_container_width=True)
        
        return "✅ Data jawaban siswa berhasil dimasukkan ke database."
        
    except Exception as e:
        st.error(f"❌ Terjadi kesalahan: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return f"❌ Error: {e}"