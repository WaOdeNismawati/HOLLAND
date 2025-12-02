import json
import numpy as np
from database.db_manager import DatabaseManager
from .anp import calculate_anp_ranking, ANPProcessor
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
    # 3️⃣ Filter jurusan berdasarkan Holland
    # ---------------------------------
    def filter_majors_by_holland(self, student_scores, top_n=15, similarity_threshold=0.7):
        """
        Filter jurusan yang cocok berdasarkan cosine similarity
        
        Args:
            student_scores: Skor RIASEC siswa (normalized)
            top_n: Jumlah jurusan yang diambil untuk ANP
            similarity_threshold: Threshold minimum similarity (0-1)
        
        Returns:
            List nama jurusan yang lolos filter
        """
        if not self.majors_data:
            print("⚠️ Data jurusan kosong, mengembalikan semua.")
            return list(self.majors_data.keys()) if self.majors_data else []

        similarities = {}
        student_vector = np.array([student_scores[h] for h in self.holland_types])

        for major, profile in self.majors_data.items():
            major_vector = np.array([profile[h] for h in self.holland_types])
            
            # Cosine Similarity
            norm_student = np.linalg.norm(student_vector)
            norm_major = np.linalg.norm(major_vector)
            
            if norm_student == 0 or norm_major == 0:
                similarities[major] = 0.0
            else:
                sim = np.dot(major_vector, student_vector) / (norm_major * norm_student)
                similarities[major] = round(float(sim), 3)

        # Filter berdasarkan threshold
        filtered = {k: v for k, v in similarities.items() if v >= similarity_threshold}
        
        # Jika terlalu sedikit, ambil top N tanpa threshold
        if len(filtered) < 5:
            filtered = dict(sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:top_n])
        
        # Ranking dan ambil top N
        ranked = sorted(filtered.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        return {
            'filtered_majors': [major for major, _ in ranked],
            'similarity_scores': dict(ranked),
            'total_filtered': len(ranked)
        }

    # ---------------------------------
    # 4️⃣ Simpan hasil ke database
    # ---------------------------------
    def save_test_result(self, student_id, scores, holland_code, top_3_types, 
                        recommended_major, anp_results=None, holland_filter=None):
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
                holland_scores, anp_results, completed_at
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            student_id,
            json.dumps(top_3_types),
            recommended_major if recommended_major else "Tidak ada rekomendasi",
            json.dumps(scores),
            json.dumps(combined_results),
            now_wita.strftime('%Y-%m-%d %H:%M:%S')
        ))

        conn.commit()
        conn.close()

    # ---------------------------------
    # 5️⃣ Proses lengkap: Holland → ANP
    # ---------------------------------
    def process_test_completion(self, student_id):
        """
        Proses lengkap sistem rekomendasi:
        1. Hitung skor RIASEC (Holland)
        2. Identifikasi Holland Code
        3. Filter jurusan berdasarkan similarity Holland
        4. Ranking jurusan hasil filter menggunakan ANP
        5. Simpan hasil
        """
        print(f"\n{'='*60}")
        print(f"🔄 Memproses hasil tes untuk student_id: {student_id}")
        print(f"{'='*60}")
        
        # STEP 1: Hitung skor Holland
        scores = self.calculate_holland_scores(student_id)
        print(f"\n📊 Skor RIASEC (Normalized):")
        for riasec, score in scores.items():
            print(f"   {riasec:15s}: {score:.3f}")
        
        # STEP 2: Identifikasi Holland Code
        holland_code, top_3_types = self.get_holland_code(scores)
        print(f"\n🎯 Holland Code: {holland_code}")
        print(f"   Top 3 Types: {', '.join(top_3_types)}")
        
        # STEP 3: Filter jurusan menggunakan Holland
        print(f"\n🔍 Filtering jurusan berdasarkan Holland similarity...")
        holland_filter_result = self.filter_majors_by_holland(
            scores, 
            top_n=15,  # Ambil 15 jurusan teratas
            similarity_threshold=0.65  # Minimum similarity 65%
        )
        
        filtered_majors = holland_filter_result['filtered_majors']
        print(f"   ✅ {len(filtered_majors)} jurusan lolos filter Holland")
        print(f"   📋 Jurusan kandidat:")
        for i, major in enumerate(filtered_majors[:5], 1):
            sim = holland_filter_result['similarity_scores'][major]
            print(f"      {i}. {major} (similarity: {sim:.3f})")
        
        # STEP 4: Ranking menggunakan ANP
        print(f"\n🧮 Menjalankan ANP untuk ranking final...")
        anp_results = None
        recommended_major = None
        
        try:
            anp_results = calculate_anp_ranking(scores, filtered_majors)
            
            if anp_results and anp_results['ranked_majors']:
                recommended_major = anp_results['ranked_majors'][0][0]
                
                print(f"   ✅ Top 5 Rekomendasi ANP:")
                for i, (major, data) in enumerate(anp_results['ranked_majors'][:5], 1):
                    print(f"      {i}. {major}: {data['anp_score']:.4f}")
            
        except Exception as e:
            print(f"   ⚠️ Error ANP: {e}")
            # Fallback: ambil jurusan dengan similarity tertinggi
            if filtered_majors:
                recommended_major = filtered_majors[0]
                print(f"   ⚠️ Menggunakan fallback (Holland top-1): {recommended_major}")
        
        # STEP 5: Simpan hasil
        print(f"\n💾 Menyimpan hasil ke database...")
        self.save_test_result(
            student_id, 
            scores, 
            holland_code,
            top_3_types, 
            recommended_major, 
            anp_results,
            holland_filter_result
        )
        
        print(f"✅ Proses selesai!")
        print(f"🎓 Rekomendasi final: {recommended_major}")
        print(f"{'='*60}\n")
        
        return {
            'scores': scores,
            'holland_code': holland_code,
            'top_3_types': top_3_types,
            'recommended_major': recommended_major,
            'holland_filter': holland_filter_result,
            'anp_results': anp_results
        }