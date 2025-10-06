import json
from database.db_manager import DatabaseManager

class HollandCalculator:
    def __init__(self):
        self.holland_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
        
        # Mapping Holland types ke jurusan
        self.major_recommendations = {
            ('Realistic', 'Investigative', 'Conventional'): 'Teknik Mesin',
            ('Realistic', 'Investigative', 'Artistic'): 'Arsitektur',
            ('Investigative', 'Realistic', 'Conventional'): 'Teknik Informatika',
            ('Investigative', 'Social', 'Artistic'): 'Psikologi',
            ('Artistic', 'Social', 'Enterprising'): 'Desain Komunikasi Visual',
            ('Social', 'Enterprising', 'Conventional'): 'Manajemen',
            ('Enterprising', 'Social', 'Conventional'): 'Administrasi Bisnis',
            ('Conventional', 'Enterprising', 'Investigative'): 'Akuntansi',
            ('Social', 'Artistic', 'Investigative'): 'Pendidikan',
            ('Realistic', 'Conventional', 'Enterprising'): 'Teknik Sipil',
            ('Investigative', 'Artistic', 'Social'): 'Kedokteran',
            ('Artistic', 'Enterprising', 'Social'): 'Komunikasi',
        }
    
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
    
    def get_top_3_types(self, scores):
        """Dapatkan 3 tipe Holland dengan skor tertinggi"""
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_scores[:3]]
    
    def recommend_major(self, top_3_types):
        """Rekomendasikan jurusan berdasarkan 3 tipe teratas"""
        top_3_tuple = tuple(top_3_types)
        
        # Cari rekomendasi yang cocok
        for key, major in self.major_recommendations.items():
            if set(key) == set(top_3_tuple):
                return major
        
        # Jika tidak ada yang cocok persis, berikan rekomendasi berdasarkan tipe pertama
        primary_type = top_3_types[0]
        fallback_recommendations = {
            'Realistic': 'Teknik Mesin',
            'Investigative': 'Teknik Informatika',
            'Artistic': 'Desain Komunikasi Visual',
            'Social': 'Psikologi',
            'Enterprising': 'Manajemen',
            'Conventional': 'Akuntansi'
        }
        
        return fallback_recommendations.get(primary_type, 'Manajemen Umum')
    
    def save_test_result(self, student_id, scores, top_3_types, recommended_major):
        """Simpan hasil tes ke database"""
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()
        
        # Hapus hasil sebelumnya jika ada
        cursor.execute('DELETE FROM test_results WHERE student_id = ?', (student_id,))
        
        # Simpan hasil baru
        cursor.execute('''
            INSERT INTO test_results (student_id, top_3_types, recommended_major, holland_scores)
            VALUES (?, ?, ?, ?)
        ''', (student_id, json.dumps(top_3_types), recommended_major, json.dumps(scores)))
        
        conn.commit()
        conn.close()
    
    def process_test_completion(self, student_id):
        """Proses lengkap setelah siswa menyelesaikan tes"""
        scores = self.calculate_holland_scores(student_id)
        top_3_types = self.get_top_3_types(scores)
        recommended_major = self.recommend_major(top_3_types)
        
        self.save_test_result(student_id, scores, top_3_types, recommended_major)
        
        return {
            'scores': scores,
            'top_3_types': top_3_types,
            'recommended_major': recommended_major
        }