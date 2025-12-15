import sqlite3
import pandas as pd
import sys

def validate_csv(csv_path):
    print('='*70)
    print('CSV VALIDATION TOOL - HOLLAND EXAM SYSTEM')
    print('='*70)
    
    # Read CSV
    try:
        df = pd.read_csv(csv_path)
        print(f'\n[OK] File berhasil dibaca')
        print(f'[OK] Total baris: {len(df)}')
        print(f'[OK] Kolom: {list(df.columns)}')
    except Exception as e:
        print(f'\n[ERROR] Gagal membaca file: {e}')
        return
    
    # Check columns
    has_student_id = 'student_id' in df.columns
    has_username = 'username' in df.columns
    has_question = 'question_id' in df.columns
    has_answer = 'answer' in df.columns
    
    print(f'\n--- Validasi Kolom ---')
    print(f'student_id atau username: {\"OK\" if (has_student_id or has_username) else \"MISSING\"}')
    print(f'question_id: {\"OK\" if has_question else \"MISSING\"}')
    print(f'answer: {\"OK\" if has_answer else \"MISSING\"}')
    
    if not (has_question and has_answer and (has_student_id or has_username)):
        print('\n[ERROR] Format CSV tidak valid!')
        return
    
    # Get DB data
    conn = sqlite3.connect('exam_system.db')
    cur = conn.cursor()
    
    cur.execute('SELECT id FROM users WHERE role=\"student\"')
    valid_student_ids = set([r[0] for r in cur.fetchall()])
    
    cur.execute('SELECT username FROM users WHERE role=\"student\"')
    valid_usernames = set([r[0] for r in cur.fetchall()])
    
    cur.execute('SELECT id FROM questions')
    valid_questions = set([r[0] for r in cur.fetchall()])
    
    conn.close()
    
    print(f'\n--- Database Info ---')
    print(f'Valid student IDs: {min(valid_student_ids)}-{max(valid_student_ids)} (total: {len(valid_student_ids)})')
    print(f'Valid question IDs: {min(valid_questions)}-{max(valid_questions)} (total: {len(valid_questions)})')
    print(f'Valid usernames: {len(valid_usernames)} accounts')
    
    # Validate CSV data
    errors = []
    warnings = []
    
    # Check student IDs
    if has_student_id:
        csv_ids = set(df['student_id'].dropna().astype(int))
        invalid_ids = csv_ids - valid_student_ids
        if invalid_ids:
            errors.append(f'Student IDs tidak valid: {sorted(invalid_ids)[:10]}')
            print(f'\n[ERROR] {len(invalid_ids)} student_id tidak ditemukan di database!')
            print(f'        Contoh: {sorted(invalid_ids)[:10]}')
    
    # Check usernames
    if has_username:
        csv_users = set(df['username'].dropna())
        invalid_users = csv_users - valid_usernames
        if invalid_users:
            errors.append(f'Usernames tidak valid: {list(invalid_users)[:5]}')
            print(f'\n[ERROR] {len(invalid_users)} username tidak ditemukan di database!')
            print(f'        Contoh: {list(invalid_users)[:5]}')
    
    # Check questions
    csv_questions = set(df['question_id'].dropna().astype(int))
    invalid_questions = csv_questions - valid_questions
    if invalid_questions:
        errors.append(f'Question IDs tidak valid: {sorted(invalid_questions)}')
        print(f'\n[ERROR] {len(invalid_questions)} question_id tidak valid!')
        print(f'        IDs: {sorted(invalid_questions)}')
    
    # Check answers
    df['answer'] = pd.to_numeric(df['answer'], errors='coerce')
    invalid_answers = df[(df['answer'] < 1) | (df['answer'] > 5) | (df['answer'].isna())]
    if len(invalid_answers) > 0:
        errors.append(f'{len(invalid_answers)} jawaban tidak valid (harus 1-5)')
        print(f'\n[ERROR] {len(invalid_answers)} jawaban tidak valid (harus 1-5)!')
    
    # Summary
    print(f'\n{\"=\"*70}')
    if errors:
        print(f'HASIL: GAGAL - {len(errors)} masalah ditemukan')
        print(f'\nMASALAH:')
        for i, err in enumerate(errors, 1):
            print(f'{i}. {err}')
    else:
        print(f'HASIL: SUKSES - CSV valid dan siap diimport!')
        print(f'\nData yang akan diimport:')
        print(f'- Total baris: {len(df)}')
        print(f'- Siswa unik: {df[\"student_id\"].nunique() if has_student_id else df[\"username\"].nunique()}')
        print(f'- Soal dijawab: {df[\"question_id\"].nunique()}')
    print('='*70)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python validate_csv.py <path_to_csv>')
        print('Example: python validate_csv.py data_jawaban.csv')
    else:
        validate_csv(sys.argv[1])
