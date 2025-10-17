import json
import pandas as pd
import numpy as np
import pandas as pd
import numpy as np
from database.db_manager import DatabaseManager
from .anp import recommend_majors

class HollandCalculator:
    def __init__(self, majors_csv_path='majors_database.csv'):
        self.holland_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
        self.majors_df = pd.read_csv(majors_csv_path)
    
    def calculate_holland_scores(self, student_id):
        """Hitung skor Holland berdasarkan jawaban siswa"""
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Ambil semua jawaban siswa dengan tipe Holland
        cursor.execute('''
            SELECT q.holland_type, sa.answer
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            WHERE sa.student_id = ?
        ''', (student_id,))
        
        answers = cursor.fetchall()
        conn.close()
        
        # Inisialisasi skor
        scores = {holland_type: 0 for holland_type in self.holland_types}
        
        # Hitung skor untuk setiap tipe
        for holland_type, answer in answers:
            scores[holland_type] += answer
        
        return scores
    
    def calculate_similarity(self, student_scores, major_profiles):
        """Hitung cosine similarity antara skor siswa dan profil jurusan"""
        student_vector = np.array([student_scores[ht] for ht in self.holland_types])
        major_vectors = major_profiles[self.holland_types].values

        # Normalisasi
        norm_student = np.linalg.norm(student_vector)
        norm_major = np.linalg.norm(major_vectors, axis=1)

        # Handle zero vector case
        if norm_student == 0 or np.any(norm_major == 0):
            return np.zeros(major_vectors.shape[0])

        # Hitung cosine similarity
        similarity = np.dot(major_vectors, student_vector) / (norm_major * norm_student)
        return similarity

    def recommend_major(self, student_scores):
        """Rekomendasikan jurusan berdasarkan skor Holland siswa menggunakan cosine similarity"""
        major_profiles = self.majors_df.copy()
        major_profiles['similarity'] = self.calculate_similarity(student_scores, major_profiles)

        # Urutkan berdasarkan similarity
        ranked_majors = major_profiles.sort_values(by='similarity', ascending=False)

        # Ambil jurusan teratas
        top_major = ranked_majors.iloc[0]['Major']
        return top_major
    
    def save_test_result(self, student_id, scores, top_3_types, recommended_major, anp_results=None):
        """Simpan hasil tes ke database dengan data ANP"""
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Hapus hasil sebelumnya jika ada
        cursor.execute('DELETE FROM test_results WHERE student_id = ?', (student_id,))
        
        # Prepare ANP data for storage
        anp_data = json.dumps(anp_results) if anp_results else None
        
        # Simpan hasil baru
        cursor.execute('''
            INSERT INTO test_results (student_id, top_3_types, recommended_major, holland_scores, anp_results)
            VALUES (?, ?, ?, ?, ?)
        ''', (student_id, json.dumps(top_3_types), recommended_major, json.dumps(scores), anp_data))
        
        conn.commit()
        conn.close()
    
    def process_test_completion(self, student_id):
        """Proses lengkap setelah siswa menyelesaikan tes dengan ANP integration"""
        scores = self.calculate_holland_scores(student_id)
        
        # Get top 3 types for compatibility and display
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_3_types = [item[0] for item in sorted_scores[:3]]

        # New recommendation based on cosine similarity
        recommended_major = self.recommend_major(scores)
        
        # ANP-based recommendations
        anp_results = recommend_majors(scores)
        
        # Get top ANP recommendation
        anp_top_major = anp_results['top_5_majors'][0][0] if anp_results['top_5_majors'] else recommended_major
        
        # Save complete results
        self.save_test_result(student_id, scores, top_3_types, anp_top_major, anp_results)
        
        return {
            'scores': scores,
            'top_3_types': top_3_types,
            'recommended_major': anp_top_major,
            'anp_results': anp_results
        }