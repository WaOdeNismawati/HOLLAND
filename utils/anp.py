"""
ANP (Analytic Network Process) Module for Decision Support System
Integrates with RIASEC Holland test results to recommend college majors
"""

import numpy as np
from scipy.linalg import eig
from database.db_manager import DatabaseManager

class ANPProcessor:
    def __init__(self, db_path="talent_test.db"):
        """
        Initialize ANP processor by loading alternatives from the database.
        """
        self.db_manager = DatabaseManager(db_path)
        self.riasec_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
        self.major_database = self._load_alternatives_from_db()

    def _load_alternatives_from_db(self):
        """
        Load college major alternatives and their RIASEC weights from the database.
        """
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT major_name, realistic, investigative, artistic, social, enterprising, conventional FROM alternatives")
        rows = cursor.fetchall()
        conn.close()

        major_db = {}
        for row in rows:
            major_name = row[0]
            weights = {
                'Realistic': row[1],
                'Investigative': row[2],
                'Artistic': row[3],
                'Social': row[4],
                'Enterprising': row[5],
                'Conventional': row[6]
            }
            major_db[major_name] = weights
        return major_db

    def build_supermatrix(self, top_3_riasec, major_weights):
        """
        Build the unweighted supermatrix W_ij.
        This matrix represents the influence of a set of elements in a component j on a set of elements in component i.
        Here, we model the influence of Criteria (j=1) on Alternatives (i=2).
        """
        criteria_names = list(top_3_riasec.keys())
        alternative_names = list(major_weights.keys())
        
        n_criteria = len(criteria_names)
        n_alternatives = len(alternative_names)
        
        # W21: Influence of Criteria on Alternatives
        w21 = np.zeros((n_alternatives, n_criteria))
        for j, criterion in enumerate(criteria_names):
            # Get the weights of all alternatives for a single criterion
            col = np.array([major_weights[alt].get(criterion, 0) for alt in alternative_names])
            # Normalize the column so it's stochastic
            col_sum = np.sum(col)
            if col_sum > 0:
                w21[:, j] = col / col_sum
        
        # The full supermatrix combines clusters. For this problem, we only need W21
        # as criteria are independent and alternatives don't influence criteria.
        # A full supermatrix would be larger and partitioned, but W21 is the key part.
        return w21, criteria_names, alternative_names

    def recommend_majors(self, riasec_scores):
        """
        Generate major recommendations using ANP synthesis.
        """
        # 1. Identify top 3 RIASEC scores as criteria
        top_3_criteria = dict(sorted(riasec_scores.items(), key=lambda item: item[1], reverse=True)[:3])

        # 2. Build the unweighted supermatrix (in this case, the alternatives-vs-criteria block)
        w21, criteria_names, alternative_names = self.build_supermatrix(top_3_criteria, self.major_database)

        # 3. Calculate normalized criteria weights (the priority vector of criteria)
        total_score = sum(top_3_criteria.values())
        if total_score == 0:
             return {'top_3_criteria': top_3_criteria, 'ranked_majors': [], 'anp_priorities': {}}

        criteria_weights = np.array([score / total_score for score in top_3_criteria.values()])

        # 4. Synthesize to get final priorities for alternatives
        # This is equivalent to calculating the limit of a weighted supermatrix, but more direct.
        # final_priorities = W_limit * initial_priorities
        # For this structure, it simplifies to: final_priorities = W21 * criteria_weights
        final_priorities = np.dot(w21, criteria_weights)

        # 5. Rank majors based on final priorities
        major_scores = {major: priority for major, priority in zip(alternative_names, final_priorities)}
        ranked_majors = sorted(major_scores.items(), key=lambda item: item[1], reverse=True)

        return {
            'top_3_criteria': top_3_criteria,
            'ranked_majors': ranked_majors,
            'anp_priorities': major_scores
        }

def test_anp_system():
    """
    Test the ANP system with sample data.
    """
    # Initialize the database to ensure tables exist
    db_manager = DatabaseManager()
    db_manager.init_database()

    # Ensure there's data in the alternatives table for testing
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM alternatives")
    if cursor.fetchone()[0] == 0:
        print("Populating alternatives table for testing...")
        sample_majors = [
            ('Teknik Informatika', 0.6, 0.9, 0.5, 0.4, 0.6, 0.8),
            ('Psikologi', 0.2, 0.8, 0.5, 0.9, 0.4, 0.6),
            ('Manajemen', 0.3, 0.5, 0.4, 0.8, 0.9, 0.8),
            ('Seni Rupa', 0.6, 0.3, 0.9, 0.4, 0.4, 0.3),
        ]
        cursor.executemany("INSERT INTO alternatives (major_name, realistic, investigative, artistic, social, enterprising, conventional) VALUES (?,?,?,?,?,?,?)", sample_majors)
        conn.commit()
    conn.close()

    # Sample student RIASEC scores
    sample_scores = {
        'Realistic': 15,
        'Investigative': 20,
        'Artistic': 8,
        'Social': 18,
        'Enterprising': 10,
        'Conventional': 12
    }
    
    anp_processor = ANPProcessor()
    results = anp_processor.recommend_majors(sample_scores)
    
    print("ANP System Test Results:")
    print("=" * 50)
    print(f"Student's Top 3 RIASEC Scores: {results['top_3_criteria']}")
    print("\nTop Recommended Majors:")
    for major, score in results['ranked_majors'][:5]:
        print(f"- {major}: (Priority: {score:.4f})")
    
    return results

if __name__ == "__main__":
    test_anp_system()