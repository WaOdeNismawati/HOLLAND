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