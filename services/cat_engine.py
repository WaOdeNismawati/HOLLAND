import random
from typing import Dict, List, Optional

from database.db_manager import DatabaseManager


class CATHollandEngine:
    """
    Simplified Test Engine dengan Random Question Selection.
    Tidak menggunakan IRT parameters (theta, discrimination, difficulty, guessing).
    """
    
    def __init__(self, max_items: int = 60):
        self.max_items = max_items
        self.question_bank = self._load_questions()

    def _load_questions(self) -> Dict[int, Dict]:
        """Load soal dari database - hanya ambil field yang diperlukan"""
        db = DatabaseManager()
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, question_text, holland_type
            FROM questions
            ORDER BY id
            """
        )
        rows = cursor.fetchall()
        conn.close()

        question_map = {}
        for row in rows:
            question_map[row[0]] = {
                'id': row[0],
                'question_text': row[1],
                'holland_type': row[2],
            }
        return question_map

    def initialize_session(self, student_id: int) -> Dict:
        """Inisialisasi sesi tes dengan urutan soal acak"""
        # Buat urutan soal acak (semua soal)
        all_question_ids = list(self.question_bank.keys())
        random.shuffle(all_question_ids)
        
        # Gunakan SEMUA soal (tidak dibatasi)
        question_order = all_question_ids
        
        initial_question_id = question_order[0] if question_order else None
        
        return {
            'student_id': student_id,
            'answers': [],
            'asked_ids': [],
            'question_order': question_order,  # Urutan soal acak
            'current_index': 0,
            'current_question_id': initial_question_id,
            'question_start': None,
            'completed': False,
            'result': None,
            'max_questions': len(question_order),  # Semua soal
        }

    def get_question(self, question_id: int) -> Optional[Dict]:
        """Ambil data soal berdasarkan ID"""
        if question_id is None:
            return None
        return self.question_bank.get(question_id)

    def select_initial_question(self) -> Optional[Dict]:
        """Pilih soal pertama secara acak"""
        if not self.question_bank:
            return None
        question_id = random.choice(list(self.question_bank.keys()))
        return self.question_bank[question_id]

    def select_next_question(self, session: Dict) -> Optional[Dict]:
        """Pilih soal berikutnya dari urutan acak"""
        next_index = session['current_index'] + 1
        
        if next_index >= len(session['question_order']):
            return None
        
        next_question_id = session['question_order'][next_index]
        return self.question_bank.get(next_question_id)

    def should_stop(self, answered: int, session: Dict) -> bool:
        """Cek apakah tes sudah selesai"""
        if answered == 0:
            return False
        if answered >= session['max_questions']:
            return True
        return False
