import json
import numpy as np
from database.db_manager import DatabaseManager
from .anp import ANPProcessor
from datetime import datetime, timedelta, timezone

WITA = timezone(timedelta(hours=8))
now_wita = datetime.now(WITA)


class HollandCalculator:
    def __init__(self):
        """Initialize Holland Calculator"""
        self.holland_types = [
            'Realistic', 'Investigative', 'Artistic',
            'Social', 'Enterprising', 'Conventional'
        ]
        
        # Load data jurusan dari database
        anp = ANPProcessor()
        try:
            self.majors_data = anp.load_majors_from_db()
        except Exception as e:
            print(f"Warning: Gagal memuat data majors - {e}")
            self.majors_data = {}

    # ---------------------------------
    # 1️⃣ Hitung skor Holland (RIASEC)
    # ---------------------------------
    def calculate_holland_scores(self, student_id):
        """Hitung skor RIASEC siswa berdasarkan jawaban dari database"""
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT q.holland_type, sa.answer
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            WHERE sa.student_id = ?
        ''', (student_id,))

        answers = cursor.fetchall()
        conn.close()

        # Inisialisasi skor
        scores = {h: 0 for h in self.holland_types}
        for holland_type, answer in answers:
            scores[holland_type] += answer

        # Normalisasi ke rentang 0–1
        max_score = max(scores.values()) if max(scores.values()) > 0 else 1
        normalized_scores = {k: round(v / max_score, 3) for k, v in scores.items()}

        return normalized_scores

    # ---------------------------------
    # 2️⃣ Identifikasi Holland Code
    # ---------------------------------
    def get_holland_code(self, scores):
        """
        Dapatkan Holland Code 3 huruf (misal: RIA, ISE)
        Berdasarkan 3 tipe tertinggi
        """
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_3 = [t[0] for t in sorted_types[:3]]
        
        # Konversi ke kode huruf
        code_map = {
            'Realistic': 'R',
            'Investigative': 'I',
            'Artistic': 'A',
            'Social': 'S',
            'Enterprising': 'E',
            'Conventional': 'C'
        }
        
        holland_code = ''.join([code_map[t] for t in top_3])
        return holland_code, top_3

    # ---------------------------------
    # 3️⃣ Metadata Dummy (Cosine Similarity Dihapus)
    # ---------------------------------
    def get_all_majors_metadata(self):
        """Kembalikan semua jurusan dengan similarity dummy 1.0"""
        if not self.majors_data:
            return {'filtered_majors': [], 'similarity_scores': {}}
            
        majors = list(self.majors_data.keys())
        similarities = {m: 1.0 for m in majors}
        
        return {
            'filtered_majors': majors,
            'similarity_scores': similarities
        }

    # ---------------------------------
    # 4️⃣ Fungsi Jalankan ANP
    # ---------------------------------
    def run_anp_logic(self, scores):
        """Menjalankan logika Pure ANP untuk semua jurusan."""
        from .anp import ANPProcessor
        anp = ANPProcessor()
        # Menggunakan calculate_anp_scores (Pure ANP)
        anp_results = anp.calculate_anp_scores(scores)

        # Tambahkan similarity dummy agar UI tidak error
        for major, data in anp_results['ranked_majors']:
            data['similarity'] = 1.0

        for item in anp_results['top_5_majors']:
            item['similarity'] = 1.0

        anp_results['methodology'] = 'Pure ANP (Analytic Network Process)'
        return anp_results

    # ---------------------------------
    # 5️⃣ Simpan hasil ke database
    # ---------------------------------
    def save_test_result(self, student_id, scores, holland_code, top_3_types, 
                        recommended_major, anp_results=None, holland_filter=None,
                        total_items=None):
        """Simpan hasil tes siswa ke tabel test_results"""
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Hapus data lama
        cursor.execute('DELETE FROM test_results WHERE student_id = ?', (student_id,))

        # Gabungkan hasil Holland dan ANP
        combined_results = {
            'holland_code': holland_code,
            'holland_filter': holland_filter,
            'anp_results': anp_results
        }

        cursor.execute('''
            INSERT INTO test_results (
                student_id, top_3_types, recommended_major,
                holland_scores, anp_results, total_items, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            student_id,
            json.dumps(top_3_types),
            recommended_major if recommended_major else "Tidak ada rekomendasi",
            json.dumps(scores),
            json.dumps(combined_results),
            total_items,
            now_wita.strftime('%Y-%m-%d %H:%M:%S')
        ))

        conn.commit()
        conn.close()

    # ---------------------------------
    # 6️⃣ PROSES UTAMA (FINAL & BERSIH)
    # ---------------------------------
    def process_test_completion(self, student_id, total_items=None):
        """Alur utama penyelesaian tes: Skor Holland -> Pure ANP -> Simpan."""
        # STEP 1: Skor Holland (RIASEC)
        scores = self.calculate_holland_scores(student_id)

        # STEP 2: Holland Code
        holland_code, top_3_types = self.get_holland_code(scores)

        # STEP 3: Metadata Dummy (Hapus Cosine Similarity Filtering)
        metadata = self.get_all_majors_metadata()
        holland_filter = metadata # Simpan sebagai holland_filter untuk kompatibilitas DB

        # STEP 4: ANP Ranking (Pure ANP pada semua jurusan)
        anp_results = None
        recommended_major = "Tidak ada rekomendasi"

        try:
            anp_results = self.run_anp_logic(scores)
            if anp_results and anp_results['ranked_majors']:
                recommended_major = anp_results['ranked_majors'][0][0]
        except Exception as e:
            print(f"Error ANP: {e}")
            # Fallback jika ANP gagal
            if metadata['filtered_majors']:
                recommended_major = metadata['filtered_majors'][0]

        # STEP 5: Simpan ke Database
        self.save_test_result(
            student_id,
            scores,
            holland_code,
            top_3_types,
            recommended_major,
            anp_results,
            holland_filter,
            total_items
        )

        return {
            'scores': scores,
            'holland_code': holland_code,
            'top_3_types': top_3_types,
            'recommended_major': recommended_major,
            'holland_filter': holland_filter,
            'anp_results': anp_results
        }