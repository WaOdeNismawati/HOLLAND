import pandas as pd
from datetime import datetime, timedelta, timezone

from src.infrastructure.database.db_manager import DatabaseManager

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
        # # Insert ke DB
        # df.to_sql("users", conn, if_exists="append", index=False)
        # print("✅ Data berhasil dimasukkan ke database.")
        # return "✅ Data berhasil dimasukkan ke database."

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