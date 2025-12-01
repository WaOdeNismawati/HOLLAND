import streamlit as st
from services.read_csv import (
    save_csv_to_db_student, 
    save_csv_to_db_soal, 
    save_csv_to_db_majors,
    save_csv_to_db_student_answers  # ✅ Import fungsi baru
)


def upload_csv_student_page():
    st.write("Unggah File CSV data Siswa")
    st.write("Silakan unggah file CSV yang berisi data Siswa Anda. File ini akan disimpan ke dalam database.")
    with st.form("upload_form"):
        file = st.file_uploader("Unggah file CSV data Siswa Anda", type=["csv", "xls", "xlsx"])
        submit_button = st.form_submit_button("Unggah dan Simpan")

    if submit_button and file:
        result = save_csv_to_db_student(file)
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)


def upload_csv_soal_page():
    st.write("Unggah File CSV Soal")
    st.write("Silakan unggah file CSV yang berisi soal-soal tes Holland. File ini akan disimpan ke dalam database.")
    with st.form("upload_form_soal"):
        file = st.file_uploader("Unggah file CSV soal", type=["csv", "xls", "xlsx"])
        submit_button = st.form_submit_button("Unggah dan Simpan")

    if submit_button and file:
        result = save_csv_to_db_soal(file)
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)


def upload_csv_majors_page():
    st.write("Unggah File CSV Majors")
    st.write("Silakan unggah file CSV yang berisi data-data majors. File ini akan disimpan ke dalam database.")
    with st.form("upload_form_majors"):
        file = st.file_uploader("Unggah file CSV Majors", type=["csv", "xls", "xlsx"])
        submit_button = st.form_submit_button("Unggah dan Simpan")

    if submit_button and file:
        result = save_csv_to_db_majors(file)
        if "✅" in result:
            st.success(result)
        else:
            st.error(result)


def upload_csv_student_answers_page():
    """Halaman upload jawaban siswa"""
    st.write("📤 Unggah File CSV Jawaban Siswa")
    st.write("Silakan unggah file CSV yang berisi jawaban siswa untuk tes Holland. File ini akan disimpan ke dalam database.")
    
    # Info format
    with st.expander("ℹ️ Format File CSV yang Diterima", expanded=False):
        st.markdown("""
        **Format 1 (Menggunakan student_id):**
```csv
        student_id,question_id,answer
        1,1,4
        1,2,5
        2,1,3
```
        
        **Format 2 (Menggunakan username):**
```csv
        username,question_id,answer
        siswa001,1,4
        siswa001,2,5
        siswa002,1,3
```
        
        **Keterangan:**
        - `student_id` atau `username`: ID atau username siswa
        - `question_id`: ID soal (1-60)
        - `answer`: Jawaban siswa (1-5)
        
        **Catatan Penting:**
        - File bisa berformat `.csv`, `.xls`, atau `.xlsx`
        - Jika ada duplikat (student_id + question_id sama), data lama akan di-update
        - Jawaban harus dalam rentang 1-5
        - Username/student_id harus terdaftar di database
        - question_id harus valid (sesuai soal yang ada)
        """)
        
        # Template download
        template_csv = "student_id,question_id,answer\n1,1,4\n1,2,5\n1,3,3\n1,4,4\n1,5,5"
        st.download_button(
            label="📥 Download Template CSV",
            data=template_csv,
            file_name="template_jawaban_siswa.csv",
            mime="text/csv",
            help="Download template untuk mempermudah pengisian data"
        )
    
    # Form upload
    with st.form("upload_form_answers"):
        file = st.file_uploader(
            "Pilih file CSV/Excel jawaban siswa",
            type=["csv", "xls", "xlsx"],
            help="Upload file berisi jawaban siswa dalam format yang sesuai"
        )
        submit_button = st.form_submit_button("📤 Upload & Proses Data", type="primary")

    if submit_button and file:
        save_csv_to_db_student_answers(file)