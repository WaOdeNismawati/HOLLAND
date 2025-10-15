import json
from database.db_manager import DatabaseManager
from utils.anp import ANPProcessor

class HollandCalculator:
    def __init__(self, db_path="talent_test_baruku.db"):
        self.db_manager = DatabaseManager(db_path)
        self.anp_processor = ANPProcessor(db_path)
        self.holland_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']

    def calculate_holland_scores(self, result_id):
        """Calculate Holland scores for a specific test result."""
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT q.holland_type, sa.answer
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            WHERE sa.result_id = ?
        ''', (result_id,))
        
        answers = cursor.fetchall()
        conn.close()
        
        scores = {holland_type: 0 for holland_type in self.holland_types}
        for holland_type, answer in answers:
            scores[holland_type] += answer
        
        return scores

    def process_test_completion(self, student_id, answers):
        """
        Orchestrates the entire test processing for a new test attempt.
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()


        try:
            # 1. Create placeholder result to get a unique ID for this test attempt
            print(cursor.execute(
                "INSERT INTO test_results (student_id, holland_scores, anp_results) VALUES (?, ?, ?)",
                (student_id, '{}', '{}')
            ))
            cursor.execute(
                "INSERT INTO test_results (student_id, holland_scores, anp_results) VALUES (?, ?, ?)",
                (student_id, '{}', '{}')
            )
            result_id = cursor.lastrowid

            # 2. Save the answers for this specific test attempt
            for question_id, answer in answers.items():
                cursor.execute(
                    "INSERT INTO student_answers (student_id, result_id, question_id, answer) VALUES (?, ?, ?, ?)",
                    (student_id, result_id, question_id, answer)
                )

            # 3. Calculate scores using only the answers for this result_id
            scores = self.calculate_holland_scores(result_id)

            # 4. Run ANP analysis
            anp_results = self.anp_processor.recommend_majors(scores)

            # 5. Save top 3 criteria to the `criteria` table
            if anp_results and 'top_3_criteria' in anp_results:
                top_3 = anp_results['top_3_criteria']
                for riasec_type, score in top_3.items():
                    cursor.execute(
                        "INSERT INTO criteria (result_id, riasec_type, score) VALUES (?, ?, ?)",
                        (result_id, riasec_type, score)
                    )

            # 6. Update the placeholder result with the actual scores and ANP data
            cursor.execute(
                "UPDATE test_results SET holland_scores = ?, anp_results = ? WHERE id = ?",
                (json.dumps(scores), json.dumps(anp_results), result_id)
            )

            conn.commit()
            print("hit")
            print(scores, anp_results)

            return {
                'scores': scores,
                'anp_results': anp_results
            }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()