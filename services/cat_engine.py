import math
from typing import Dict, List, Optional

from database.db_manager import DatabaseManager


class CATHollandEngine:
    def __init__(self, min_items: int = 18, max_items: Optional[int] = None,
                 target_se: float = 0.35, learning_rate: float = 0.5):
        self.min_items = min_items
        self.max_items = max_items
        self.target_se = target_se
        self.learning_rate = learning_rate
        self.question_bank = self._load_questions()
        self.total_questions = len(self.question_bank)
        self.require_full_bank = max_items is None

        if self.require_full_bank:
            self.active_max_items = self.total_questions
        else:
            if self.total_questions and max_items is not None:
                self.active_max_items = min(max_items, self.total_questions)
            else:
                self.active_max_items = max_items

        if not self.active_max_items:
            self.active_max_items = self.total_questions

    def _load_questions(self) -> Dict[int, Dict]:
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
        initial_question = self.select_initial_question()
        return {
            'student_id': student_id,
            'theta': 0.0,
            'theta_history': [],
            'information': 0.0,
            'answers': [],
            'asked_ids': [],
            'current_question_id': initial_question['id'] if initial_question else None,
            'question_start': None,
            'completed': False,
            'result': None,
            'max_questions': self.active_max_items,
            'se': None
        }

    def get_question(self, question_id: int) -> Optional[Dict]:
        if question_id is None:
            return None
        return self.question_bank.get(question_id)

    def select_initial_question(self) -> Optional[Dict]:
        # Pilih soal pertama secara random
        import random
        candidates = list(self.question_bank.values())
        return random.choice(candidates) if candidates else None

    def select_next_question(self, theta: float, asked_ids: List[int]) -> Optional[Dict]:
        return self._select_question_by_target(theta, asked_ids)

    def _select_question_by_target(self, theta: float, asked_ids: List[int]) -> Optional[Dict]:
        candidates = [
            q for q in self.question_bank.values()
            if q['id'] not in asked_ids
        ]
        if not candidates:
            return None

        # Cek tipe Holland dari soal terakhir yang dijawab
        last_holland_type = None
        if asked_ids:
            last_question = self.question_bank.get(asked_ids[-1])
            if last_question:
                last_holland_type = last_question['holland_type']
        
        # Prioritaskan soal dengan tipe Holland yang BERBEDA dari soal terakhir
        if last_holland_type:
            different_type_candidates = [q for q in candidates if q['holland_type'] != last_holland_type]
            # Jika masih ada soal dengan tipe berbeda, gunakan itu
            if different_type_candidates:
                candidates = different_type_candidates
        
        # Pilih soal secara random dari kandidat
        import random
        return random.choice(candidates) if candidates else None

    def should_stop(self, answered: int, current_se: Optional[float]) -> bool:
        if answered == 0:
            return False
        if self.require_full_bank:
            return answered >= self.total_questions
        if self.active_max_items and answered >= self.active_max_items:
            return True
        if answered >= self.min_items and current_se is not None and current_se <= self.target_se:
            return True
        return False
