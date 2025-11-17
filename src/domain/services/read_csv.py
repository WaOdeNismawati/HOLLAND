import pandas as pd
from datetime import datetime, timedelta, timezone

from src.core.auth import hash_password
from src.infrastructure.database.db_manager import DatabaseManager

WITA = timezone(timedelta(hours=8))


def save_csv_to_db_student(file_csv: str):
    try:
        if not file_csv:
            raise ValueError("File CSV tidak ditemukan.")

        df = pd.read_csv(file_csv)
        required_columns = ["username", "password", "full_name", "class_name"]

        df = df[required_columns]
        df = df.fillna({"class_name": ""})

        conn = DatabaseManager().get_connection()
        cursor = conn.cursor()

        records = []
        for _, row in df.iterrows():
            username = str(row["username"]).strip()
            password = str(row["password"])
            full_name = str(row["full_name"]).strip()
            class_name = str(row["class_name"]).strip()

            if not username or not password or not full_name:
                continue

            hashed_password = hash_password(password)
            records.append((
                username,
                hashed_password,
                "student",
                full_name,
                class_name if class_name else None,
                datetime.now(WITA).strftime('%Y-%m-%d %H:%M:%S')
            ))

        if not records:
            return "❌ Tidak ada baris valid yang ditemukan pada file."

        cursor.executemany(
            '''
            INSERT OR IGNORE INTO users (username, password, role, full_name, class_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ''',
            records
        )

        conn.commit()

        inserted = cursor.rowcount if cursor.rowcount != -1 else len(records)
        return f"✅ {inserted} data siswa berhasil dimasukkan ke database."

    except Exception as e:
        return f"❌ Error: {e}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()

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