import json
from database.db_manager import DatabaseManager
from utils.anp import ANPProcessor

class HollandCalculator:
    def __init__(self, db_path="talent_test.db"):
        self.db_manager = DatabaseManager(db_path)
        self.anp_processor = ANPProcessor(db_path)
        self.holland_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']

    def calculate_holland_scores(self, student_id):
        """Calculate Holland scores based on student's answers."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT q.holland_type, sa.answer
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            WHERE sa.student_id = ?
        ''', (student_id,))
        
        answers = cursor.fetchall()
        conn.close()
        
        scores = {holland_type: 0 for holland_type in self.holland_types}
        for holland_type, answer in answers:
            scores[holland_type] += answer
        
        return scores

    def get_top_3_types(self, scores):
        """Get the top 3 Holland types from scores."""
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_scores[:3]]

    def save_test_result(self, student_id, scores, top_3_types, recommended_major, anp_results):
        """Save the test result, overwriting any previous result."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()

        # Delete previous result to enforce one-result-per-student
        cursor.execute('DELETE FROM test_results WHERE student_id = ?', (student_id,))

        anp_data = json.dumps(anp_results) if anp_results else None

        cursor.execute('''
            INSERT INTO test_results (student_id, holland_scores, anp_results, top_3_types, recommended_major)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, json.dumps(scores), anp_data, json.dumps(top_3_types), recommended_major))

        conn.commit()
        conn.close()

    def process_test_completion(self, student_id, answers):
        """
        Process test completion, calculate scores, run ANP, and save the single result.
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        # Overwrite previous answers
        try:
            cursor.execute('DELETE FROM student_answers WHERE student_id = ?', (student_id,))
            for question_id, answer in answers.items():
                cursor.execute(
                    "INSERT INTO student_answers (student_id, question_id, answer) VALUES (?, ?, ?)",
                    (student_id, question_id, answer)
                )
            conn.commit()
        finally:
            conn.close()

        scores = self.calculate_holland_scores(student_id)
        anp_results = self.anp_processor.recommend_majors(scores)
        top_3_types = self.get_top_3_types(scores)

        recommended_major = anp_results['ranked_majors'][0][0] if anp_results.get('ranked_majors') else "N/A"

        self.save_test_result(student_id, scores, top_3_types, recommended_major, anp_results)

        return {
            'scores': scores,
            'anp_results': anp_results,
            'top_3_types': top_3_types,
            'recommended_major': recommended_major
        }