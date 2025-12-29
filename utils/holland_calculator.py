import json
import numpy as np
from database.db_manager import DatabaseManager
from .anp import calculate_anp_ranking, calculate_hybrid_ranking, ANPProcessor
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
    # 3️⃣ Simpan hasil ke database
    # ---------------------------------
    def save_test_result(self, student_id, scores, holland_code, top_3_types, 
                        recommended_major, anp_results=None, total_items=None):
        """Simpan hasil tes siswa ke tabel test_results"""
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Hapus data lama
        cursor.execute('DELETE FROM test_results WHERE student_id = ?', (student_id,))

        # Gabungkan hasil Holland dan ANP
        combined_results = {
            'holland_code': holland_code,
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
    # 4️⃣ Proses lengkap: Holland → Hybrid Ranking
    # ---------------------------------
    def process_test_completion(self, student_id, total_items=None):
        """
        Proses lengkap sistem rekomendasi:
        1. Hitung skor RIASEC (Holland)
        2. Identifikasi Holland Code
        3. Ranking semua jurusan menggunakan Hybrid Method:
           - ANP untuk criteria weighting (bobot kriteria)
           - Weighted scoring untuk ranking jurusan
           - Cosine similarity sebagai bonus
        4. Simpan hasil
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
        
        # STEP 3: Ranking menggunakan ANP Murni (Supermatrix + Limit Matrix)
        print(f"\n🧮 Menjalankan ANP Murni (Supermatrix + Inner Dependency)...")
        anp_results = None
        recommended_major = None
        
        total_majors = len(self.majors_data)
        print(f"   📊 Total {total_majors} jurusan akan dianalisis")
        
        try:
            # Jalankan ANP Murni untuk semua jurusan dari database
            anp_results = calculate_anp_ranking(scores)
            
            if anp_results and anp_results['ranked_majors']:
                recommended_major = anp_results['ranked_majors'][0][0]
                
                print(f"   ✅ Top 5 Rekomendasi:")
                for i, (major, data) in enumerate(anp_results['ranked_majors'][:5], 1):
                    anp_score = data.get('anp_score', 0)
                    print(f"      {i}. {major}: {anp_score:.4f}")
            
        except Exception as e:
            print(f"   ⚠️ Error ANP: {e}")
            # Fallback: ambil jurusan pertama dari database
            if self.majors_data:
                recommended_major = list(self.majors_data.keys())[0]
                print(f"   ⚠️ Menggunakan fallback: {recommended_major}")
        
        # STEP 4: Simpan hasil
        print(f"\n💾 Menyimpan hasil ke database...")
        self.save_test_result(
            student_id, 
            scores, 
            holland_code,
            top_3_types, 
            recommended_major, 
            anp_results,
            total_items
        )
        
        print(f"✅ Proses selesai!")
        print(f"🎓 Rekomendasi final: {recommended_major}")
        print(f"{'='*60}\n")
        
        return {
            'scores': scores,
            'holland_code': holland_code,
            'top_3_types': top_3_types,
            'recommended_major': recommended_major,
            'anp_results': anp_results
        }