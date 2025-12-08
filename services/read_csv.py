import io
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta, timezone
import unicodedata
import traceback

from database.db_manager import DatabaseManager
from utils.auth import hash_password

WITA = timezone(timedelta(hours=8))


# -------------------------
# Helper util
# -------------------------
def _try_read_csv(file_like):
    """
    Try read CSV with multiple encodings. Return pandas.DataFrame.
    """
    encodings = ["utf-8", "latin1", "cp1252"]
    last_exc = None
    for enc in encodings:
        try:
            # If file_like is an UploadedFile (Streamlit), .read() moves pointer, so we reset using BytesIO
            if hasattr(file_like, "read") and not isinstance(file_like, str):
                raw = file_like.read()
                # reset pointer for future ops
                try:
                    file_like.seek(0)
                except Exception:
                    pass
                df = pd.read_csv(io.BytesIO(raw), encoding=enc)
            else:
                df = pd.read_csv(file_like, encoding=enc)
            return df
        except Exception as e:
            last_exc = e
            # try next encoding
            continue
    # if all fail, raise last exception
    raise last_exc


def _normalize_text(s):
    """Trim, normalize unicode, remove zero-width spaces etc."""
    if pd.isna(s):
        return s
    if not isinstance(s, str):
        s = str(s)
    s = s.strip()
    s = unicodedata.normalize("NFC", s)
    # remove weird control chars
    s = "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")
    return s


def _auto_rename_columns(cols):
    """
    Map common alternative column names to expected ones.
    Returns mapping dict for dataframe.rename(...)
    """
    mapping = {}
    col_candidates = {c.lower(): c for c in cols}

    # student fields
    if "username" in col_candidates:
        mapping[col_candidates["username"]] = "username"
    if "user name" in col_candidates:
        mapping[col_candidates["user name"]] = "username"
    if "user" in col_candidates:
        mapping[col_candidates["user"]] = "username"
    if "password" in col_candidates:
        mapping[col_candidates["password"]] = "password"
    if "full_name" in col_candidates:
        mapping[col_candidates["full_name"]] = "full_name"
    if "full name" in col_candidates:
        mapping[col_candidates["full name"]] = "full_name"
    if "name" in col_candidates and "full_name" not in mapping:
        mapping[col_candidates["name"]] = "full_name"
    if "class_name" in col_candidates:
        mapping[col_candidates["class_name"]] = "class_name"
    if "class" in col_candidates and "class_name" not in mapping:
        mapping[col_candidates["class"]] = "class_name"

    # answers fields
    if "student_id" in col_candidates:
        mapping[col_candidates["student_id"]] = "student_id"
    if "question_id" in col_candidates:
        mapping[col_candidates["question_id"]] = "question_id"
    if "answer" in col_candidates:
        mapping[col_candidates["answer"]] = "answer"
    if "username" in col_candidates and "student_id" not in mapping:
        # keep username as-is (some CSV use username + question_id + answer)
        pass

    # questions fields
    if "question_text" in col_candidates:
        mapping[col_candidates["question_text"]] = "question_text"
    if "holland_type" in col_candidates:
        mapping[col_candidates["holland_type"]] = "holland_type"
    if "type" in col_candidates and "holland_type" not in mapping:
        mapping[col_candidates["type"]] = "holland_type"

    # majors fields
    maj_candidates = ["major", "Major", "Major Name", "major_name"]
    for k, v in col_candidates.items():
        low = k.lower()
        if low in ["major", "major_name", "major name"]:
            mapping[v] = "Major"
        if low in ["realistic", "investigative", "artistic", "social", "enterprising", "conventional"]:
            mapping[v] = v.capitalize()

    return mapping


def _as_custom_userid(raw_id):
    """Convert input student identifier to integer id used in database."""
    if pd.isna(raw_id):
        return None
    s = str(raw_id).strip()
    if s == "":
        return None

    # format U123
    if s[0].upper() == "U" and s[1:].isdigit():
        return int(s[1:])

    # numeric string / float string
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _as_custom_questionid(raw_q):
    """Convert input question identifier to integer id."""
    if pd.isna(raw_q):
        return None
    s = str(raw_q).strip()
    if s == "":
        return None
    if s[0].upper() == "Q" and s[1:].isdigit():
        return int(s[1:])
    try:
        return int(float(s))
    except (ValueError, TypeError):
        return None


def _reset_sequence_if_table_empty(conn, table_name):
    """Reset AUTOINCREMENT sequence when the table currently has no rows."""
    try:
        cur = conn.cursor()
        cur.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cur.fetchone()[0]
        if count == 0:
            cur.execute("DELETE FROM sqlite_sequence WHERE name=?", (table_name,))
            conn.commit()
    except Exception:
        pass


# -------------------------
# Main import functions
# -------------------------
def save_csv_to_db_student(file_csv):
    """
    Import students CSV.
    Expected columns (auto-rename supported): username, password, full_name, class_name
    """
    db = DatabaseManager()
    conn = None
    inserted = 0
    skipped = 0
    errors = 0
    try:
        # read csv with encoding fallback
        if hasattr(file_csv, "name") and (file_csv.name.endswith(".xls") or file_csv.name.endswith(".xlsx")):
            df = pd.read_excel(file_csv)
        else:
            df = _try_read_csv(file_csv)

        if df is None or df.shape[0] == 0:
            return "❌ Error: File kosong atau tidak terbaca."

        # auto rename columns
        rename_map = _auto_rename_columns(list(df.columns))
        if rename_map:
            df = df.rename(columns=rename_map)

        required = ["username", "password", "full_name", "class_name"]
        missing = [c for c in required if c not in df.columns]
        # allow class_name to be optional
        if "class_name" in missing:
            # not fatal: fill with None
            df["class_name"] = None
            missing = [c for c in missing if c != "class_name"]

        if missing:
            return f"❌ Format CSV tidak valid. Kolom hilang: {missing}"

        # clean & normalize columns
        for c in ["username", "password", "full_name", "class_name"]:
            df[c] = df[c].apply(_normalize_text)

        # add role and created_at
        now = datetime.now(WITA).isoformat(sep=" ", timespec="seconds")

        conn = db.get_connection()
        cursor = conn.cursor()

        _reset_sequence_if_table_empty(conn, "users")

        cursor.execute("BEGIN")
        for _, row in df.iterrows():
            try:
                username = row["username"]
                password = row["password"]
                full_name = row["full_name"]
                class_name = row.get("class_name", None)

                if not username or not password or not full_name:
                    skipped += 1
                    continue

                hashed_pw = hash_password(password)

                cursor.execute("""
                    INSERT INTO users (username, password, role, full_name, class_name, created_at)
                    VALUES (?, ?, 'student', ?, ?, ?)
                """, (username, hashed_pw, full_name, class_name, now))
                if cursor.rowcount == 1:
                    user_id = cursor.lastrowid
                else:
                    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                    existing = cursor.fetchone()
                    user_id = existing[0] if existing else None

                if user_id:
                    db.ensure_student_profile(cursor, user_id, full_name, class_name)
                inserted += 1

            except Exception as exc_row:
                errors += 1
                # continue processing others
                print(f"[read_csv] Error inserting student row: {exc_row}")
                continue

        conn.commit()
        return f"✅ Data siswa berhasil dimasukkan. Inserted: {inserted}, Skipped: {skipped}, Errors: {errors}"

    except Exception as e:
        if conn:
            conn.rollback()
        print(traceback.format_exc())
        return f"❌ Error saat import siswa: {e}"


def save_csv_to_db_soal(file_csv):
    """
    Import questions CSV.
    Expected columns: question_text, holland_type (supports R/I/A/S/E/C or full names)
    """
    db = DatabaseManager()
    conn = None
    inserted = 0
    skipped = 0
    errors = 0
    try:
        # read file
        if hasattr(file_csv, "name") and (file_csv.name.endswith(".xls") or file_csv.name.endswith(".xlsx")):
            df = pd.read_excel(file_csv)
        else:
            df = _try_read_csv(file_csv)

        if df is None or df.shape[0] == 0:
            return "❌ Error: File kosong atau tidak terbaca."

        rename_map = _auto_rename_columns(list(df.columns))
        if rename_map:
            df = df.rename(columns=rename_map)

        required = ["question_text", "holland_type"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            return f"❌ Format CSV soal tidak valid. Kolom hilang: {missing}"

        # normalize
        df["question_text"] = df["question_text"].apply(_normalize_text)
        df["holland_type"] = df["holland_type"].apply(_normalize_text)

        # Map short codes to full
        mapping = {
            "R": "Realistic",
            "I": "Investigative",
            "A": "Artistic",
            "S": "Social",
            "E": "Enterprising",
            "C": "Conventional"
        }
        df["holland_type"] = df["holland_type"].apply(lambda v: mapping.get(v.upper(), v) if isinstance(v, str) else v)

        now = datetime.now(WITA).isoformat(sep=" ", timespec="seconds")

        conn = db.get_connection()
        cursor = conn.cursor()
        _reset_sequence_if_table_empty(conn, "questions")
        cursor.execute("BEGIN")
        for _, row in df.iterrows():
            try:
                qtext = row["question_text"]
                qtype = row["holland_type"]

                if not qtext or not qtype:
                    skipped += 1
                    continue

                cursor.execute("""
                    INSERT INTO questions (question_text, holland_type, created_at)
                    VALUES (?, ?, ?)
                """, (qtext, qtype, now))
                inserted += 1
            except Exception as exc_row:
                errors += 1
                print(f"[read_csv] Error inserting question row: {exc_row}")
                continue

        conn.commit()
        return f"✅ Data soal berhasil dimasukkan. Inserted: {inserted}, Skipped: {skipped}, Errors: {errors}"

    except Exception as e:
        if conn:
            conn.rollback()
        print(traceback.format_exc())
        return f"❌ Error saat import soal: {e}"


def save_csv_to_db_majors(file_csv):
    """
    Import majors CSV.
    Expected columns: Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional
    """
    db = DatabaseManager()
    conn = None
    inserted = 0
    skipped = 0
    errors = 0
    try:
        if hasattr(file_csv, "name") and (file_csv.name.endswith(".xls") or file_csv.name.endswith(".xlsx")):
            df = pd.read_excel(file_csv)
        else:
            df = _try_read_csv(file_csv)

        if df is None or df.shape[0] == 0:
            return "❌ Error: File kosong atau tidak terbaca."

        rename_map = _auto_rename_columns(list(df.columns))
        if rename_map:
            df = df.rename(columns=rename_map)

        required = ["Major", "Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"]
        missing = [c for c in required if c not in df.columns]
        if missing:
            return f"❌ Format CSV majors tidak valid. Kolom hilang: {missing}"

        # normalize text and numeric cast
        df["Major"] = df["Major"].apply(_normalize_text)
        for trait in ["Realistic", "Investigative", "Artistic", "Social", "Enterprising", "Conventional"]:
            df[trait] = pd.to_numeric(df[trait], errors="coerce").fillna(0.0)

        conn = db.get_connection()
        cursor = conn.cursor()
        _reset_sequence_if_table_empty(conn, "majors")
        cursor.execute("BEGIN")
        for _, row in df.iterrows():
            try:
                major_name = row["Major"]
                if not major_name:
                    skipped += 1
                    continue

                cursor.execute("""
                    INSERT INTO majors (Major, Realistic, Investigative, Artistic, Social, Enterprising, Conventional)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    major_name,
                    float(row["Realistic"]),
                    float(row["Investigative"]),
                    float(row["Artistic"]),
                    float(row["Social"]),
                    float(row["Enterprising"]),
                    float(row["Conventional"])
                ))
                inserted += 1
            except Exception as exc_row:
                errors += 1
                print(f"[read_csv] Error inserting major row: {exc_row}")
                continue

        conn.commit()
        return f"✅ Data jurusan berhasil dimasukkan. Inserted: {inserted}, Skipped: {skipped}, Errors: {errors}"

    except Exception as e:
        if conn:
            conn.rollback()
        print(traceback.format_exc())
        return f"❌ Error saat import majors: {e}"


def save_csv_to_db_student_answers(uploaded_file):
    """
    Import student answers CSV or Excel.
    Accept:
      - columns: student_id, question_id, answer
      - columns: username, question_id, answer
    Supports:
      - student_id numeric (1) or prefixed format (U1)
      - question_id numeric (1) or prefixed format (Q1)
    """
    db = DatabaseManager()
    conn = None

    success_count = 0
    update_count = 0
    error_count = 0
    skipped_rows = 0
    bad_rows = []

    try:
        # read file
        if hasattr(uploaded_file, "name") and (uploaded_file.name.endswith(".xls") or uploaded_file.name.endswith(".xlsx")):
            df = pd.read_excel(uploaded_file)
        else:
            df = _try_read_csv(uploaded_file)

        if df is None or df.shape[0] == 0:
            st.error("❌ File kosong atau tidak terbaca.")
            return "❌ File kosong atau tidak terbaca."

        # auto rename columns
        rename_map = _auto_rename_columns(list(df.columns))
        if rename_map:
            df = df.rename(columns=rename_map)

        required_opt1 = ["student_id", "question_id", "answer"]
        required_opt2 = ["username", "question_id", "answer"]

        use_student_id = False
        if all(col in df.columns for col in required_opt1):
            use_student_id = True
        elif all(col in df.columns for col in required_opt2):
            use_student_id = False
        else:
            st.error("❌ Format CSV tidak valid. Butuh kolom: student_id OR username, plus question_id & answer.")
            st.info(f"Kolom ditemukan: {list(df.columns)}")
            return

        # clean columns
        df_columns_before = list(df.columns)
        for c in df_columns_before:
            if df[c].dtype == object:
                df[c] = df[c].apply(_normalize_text)

        # If username provided, map to student_id
        conn = db.get_connection()
        cursor = conn.cursor()
        _reset_sequence_if_table_empty(conn, "student_answers")
        if not use_student_id:
            st.info("🔄 Mengonversi username -> student_id ...")
            cursor.execute("SELECT id, username FROM users WHERE role = 'student'")
            username_map = {row[1]: row[0] for row in cursor.fetchall()}  # username -> id
            df["student_id"] = df["username"].map(username_map)
            missing_usernames = df[df["student_id"].isna()]["username"].unique()
            if len(missing_usernames) > 0:
                st.warning(f"⚠️ Username tidak ditemukan: {', '.join(map(str, missing_usernames))}")
                # drop missing users
                df = df.dropna(subset=["student_id"])

        # Convert identifiers to integer IDs
        df["student_id"] = df["student_id"].apply(_as_custom_userid)
        df["question_id"] = df["question_id"].apply(_as_custom_questionid)

        # Ensure answer numeric
        df["answer"] = pd.to_numeric(df["answer"], errors="coerce")

        # Validate answer range
        invalid_answers = df[(df["answer"] < 1) | (df["answer"] > 5) | (df["answer"].isna())]
        if len(invalid_answers) > 0:
            st.warning(f"⚠️ Ditemukan {len(invalid_answers)} baris dengan jawaban tidak valid (1-5). Baris ini akan diabaikan.")
            df = df[~df.index.isin(invalid_answers.index)]

        # Validate student_id exists
        cursor.execute("SELECT id FROM users WHERE role = 'student'")
        valid_student_ids = {row[0] for row in cursor.fetchall()}
        invalid_students = df[~df["student_id"].isin(valid_student_ids)]
        if len(invalid_students) > 0:
            st.warning(f"⚠️ Ditemukan {len(invalid_students)} baris dengan student_id tidak valid. Baris ini diabaikan.")
            df = df[df["student_id"].isin(valid_student_ids)]

        # Validate question_id exists
        cursor.execute("SELECT id FROM questions")
        valid_question_ids = {row[0] for row in cursor.fetchall()}
        invalid_questions = df[~df["question_id"].isin(valid_question_ids)]
        if len(invalid_questions) > 0:
            st.warning(f"⚠️ Ditemukan {len(invalid_questions)} baris dengan question_id tidak valid. Baris ini diabaikan.")
            df = df[df["question_id"].isin(valid_question_ids)]

        if len(df) == 0:
            st.error("❌ Tidak ada data valid untuk disimpan setelah validasi.")
            conn.close()
            return "❌ Tidak ada data valid untuk disimpan."

        # Setup progress bar
        total_rows = len(df)
        progress_bar = st.progress(0)
        status_text = st.empty()

        # Insert/update rows
        cursor.execute("BEGIN")
        for idx, row in df.iterrows():
            try:
                sid = row["student_id"]
                qid = row["question_id"]
                ans = int(row["answer"])

                # check existing
                cursor.execute("""
                    SELECT id FROM student_answers WHERE student_id = ? AND question_id = ?
                """, (sid, qid))
                existing = cursor.fetchone()
                if existing:
                    cursor.execute("""
                        UPDATE student_answers SET answer = ?, created_at = datetime('now', '+8 hours')
                        WHERE student_id = ? AND question_id = ?
                    """, (ans, sid, qid))
                    update_count += 1
                else:
                    cursor.execute("""
                        INSERT INTO student_answers (student_id, question_id, answer, created_at)
                        VALUES (?, ?, ?, datetime('now', '+8 hours'))
                    """, (sid, qid, ans))
                    success_count += 1

            except Exception as exc_row:
                error_count += 1
                bad_rows.append((idx, str(exc_row)))
                print(f"[read_csv] Error processing row {idx}: {exc_row}")
                continue
            finally:
                progress = (idx + 1) / total_rows
                progress_bar.progress(progress)
                status_text.text(f"Memproses: {idx + 1}/{total_rows} baris...")

        conn.commit()
        progress_bar.empty()
        status_text.empty()
        conn.close()

        # Summary
        st.success("✅ Data berhasil diproses!")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📥 Data Baru", success_count)
        with col2:
            st.metric("🔄 Data Diupdate", update_count)
        with col3:
            st.metric("⚠️ Diabaikan", len(invalid_answers) + len(invalid_students) + len(invalid_questions))
        with col4:
            st.metric("❌ Error", error_count)

        if bad_rows:
            with st.expander("🔍 Baris yang error (preview)"):
                st.write(bad_rows[:20])

        # preview
        with st.expander("📊 Detail Upload"):
            st.write(f"**Total baris diproses:** {total_rows}")
            st.write(f"**Siswa unik:** {df['student_id'].nunique()}")
            st.write(f"**Soal dijawab:** {df['question_id'].nunique()}")
            st.write("**Preview 5 baris pertama:**")
            st.dataframe(df[["student_id", "question_id", "answer"]].head(), use_container_width=True)

        return f"✅ Data jawaban siswa berhasil dimasukkan ke database. Baru: {success_count}, Update: {update_count}, Errors: {error_count}"

    except Exception as e:
        print(traceback.format_exc())
        if conn:
            try:
                conn.rollback()
                conn.close()
            except:
                pass
        st.error(f"❌ Terjadi kesalahan saat memproses file: {e}")
        return f"❌ Error: {e}"
