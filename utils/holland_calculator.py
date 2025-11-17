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
    # 1️⃣ Hitung skor Holland (RIASEC) - FIXED!
    # ---------------------------------
    def calculate_holland_scores(self, student_id):
        """
        Hitung skor RIASEC siswa berdasarkan jawaban dari database
        
        PERBAIKAN:
        - Mengembalikan skor RAW dan NORMALIZED
        - Normalisasi menggunakan skor maksimal TEORITIS, bukan maksimal aktual
        - Lebih konsisten dan mudah dipahami
        """
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Hitung jumlah soal per tipe Holland
        cursor.execute('''
            SELECT holland_type, COUNT(*) as count
            FROM questions
            GROUP BY holland_type
        ''')
        questions_per_type = dict(cursor.fetchall())

        # Ambil jawaban siswa
        cursor.execute('''
            SELECT q.holland_type, sa.answer
            FROM student_answers sa
            JOIN questions q ON sa.question_id = q.id
            WHERE sa.student_id = ?
        ''', (student_id,))

        answers = cursor.fetchall()
        conn.close()

        # Inisialisasi skor RAW
        raw_scores = {h: 0 for h in self.holland_types}
        for holland_type, answer in answers:
            raw_scores[holland_type] += answer

        # Hitung skor MAKSIMAL TEORITIS per tipe (jumlah soal × 5)
        max_possible_scores = {
            h: questions_per_type.get(h, 0) * 5 
            for h in self.holland_types
        }
        
        # Normalisasi berdasarkan MAKSIMAL TEORITIS (0-1 scale)
        normalized_scores = {}
        for h in self.holland_types:
            if max_possible_scores[h] > 0:
                normalized_scores[h] = round(raw_scores[h] / max_possible_scores[h], 3)
            else:
                normalized_scores[h] = 0.0

        print(f"\n📊 Detail Skor RIASEC:")
        print(f"{'Tipe':<15} {'Raw':<8} {'Max':<8} {'Normalized':<12} {'Persentase'}")
        print(f"{'='*60}")
        for h in self.holland_types:
            percentage = normalized_scores[h] * 100
            print(f"{h:<15} {raw_scores[h]:<8} {max_possible_scores[h]:<8} {normalized_scores[h]:<12.3f} {percentage:.1f}%")

        return normalized_scores

    # ---------------------------------
    # 2️⃣ Identifikasi Holland Code - FIXED!
    # ---------------------------------
    def get_holland_code(self, scores):
        """
        Dapatkan Holland Code 3 huruf (misal: RIA, ISE)
        Berdasarkan 3 tipe tertinggi
        
        PERBAIKAN:
        - Return juga sorted_scores untuk konsistensi tampilan
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
        
        # Return juga sorted scores untuk transparansi
        return holland_code, top_3, sorted_types

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
            Dict dengan filtered_majors, similarity_scores, total_filtered
        """
        if not self.majors_data:
            print("⚠️ Data jurusan kosong, mengembalikan semua.")
            return {
                'filtered_majors': [],
                'similarity_scores': {},
                'total_filtered': 0
            }

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
    # 4️⃣ Simpan hasil ke database - FIXED!
    # ---------------------------------
    def save_test_result(self, student_id, scores, holland_code, top_3_types, 
                        recommended_major, anp_results=None, holland_filter=None,
                        sorted_all_scores=None):
        """
        Simpan hasil tes siswa ke tabel test_results
        
        PERBAIKAN:
        - Menyimpan sorted_all_scores untuk konsistensi tampilan
        - Memastikan data yang disimpan lengkap dan konsisten
        """
        db_manager = DatabaseManager()
        conn = db_manager.get_connection()
        cursor = conn.cursor()

        # Hapus data lama
        cursor.execute('DELETE FROM test_results WHERE student_id = ?', (student_id,))

        # Format ANP results untuk disimpan dengan struktur yang konsisten
        anp_data_to_save = None
        if anp_results:
            anp_data_to_save = {
                'student_riasec_profile': scores,  # Gunakan scores yang sama dengan holland_scores
                'sorted_riasec_scores': sorted_all_scores,  # Tambahkan ini untuk konsistensi
                'top_5_majors': [
                    {
                        'major_name': major,
                        'anp_score': data['anp_score'],
                        'riasec_profile': data.get('riasec_profile', {}),
                        'criteria_weights': data.get('criteria_weights', {}),
                        'criteria_priorities': data.get('criteria_priorities', {})
                    }
                    for major, data in anp_results.get('top_5_majors', [])
                ],
                'holland_filter': holland_filter,
                'total_analyzed': anp_results.get('total_analyzed', 0),
                'methodology': 'True ANP + Holland Filtering',
                'calculation_details': anp_results.get('calculation_details', {})
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
            json.dumps(anp_data_to_save) if anp_data_to_save else None,
            now_wita.strftime('%Y-%m-%d %H:%M:%S')
        ))

        conn.commit()
        conn.close()

    # ---------------------------------
    # 5️⃣ Proses lengkap: Holland → ANP - FIXED!
    # ---------------------------------
    def process_test_completion(self, student_id):
        """
        Proses lengkap sistem rekomendasi:
        1. Hitung skor RIASEC (Holland) dengan normalisasi yang benar
        2. Identifikasi Holland Code
        3. Filter jurusan berdasarkan similarity Holland
        4. Ranking jurusan hasil filter menggunakan ANP
        5. Simpan hasil dengan data yang konsisten
        """
        print(f"\n{'='*60}")
        print(f"📄 Memproses hasil tes untuk student_id: {student_id}")
        print(f"{'='*60}")
        
        # STEP 1: Hitung skor Holland dengan normalisasi yang benar
        scores = self.calculate_holland_scores(student_id)
        
        # STEP 2: Identifikasi Holland Code dengan sorted scores
        holland_code, top_3_types, sorted_all_scores = self.get_holland_code(scores)
        
        print(f"\n🎯 Holland Code: {holland_code}")
        print(f"   Top 3 Types:")
        for i, (h_type, score) in enumerate(sorted_all_scores[:3], 1):
            print(f"   {i}. {h_type}: {score:.3f} ({score*100:.1f}%)")
        
        # STEP 3: Filter jurusan menggunakan Holland
        print(f"\n🔍 Filtering jurusan berdasarkan Holland similarity...")
        holland_filter_result = self.filter_majors_by_holland(
            scores, 
            top_n=15,  # Ambil 15 jurusan teratas
            similarity_threshold=0.65  # Minimum similarity 65%
        )
        
        filtered_majors = holland_filter_result['filtered_majors']
        print(f"   ✅ {len(filtered_majors)} jurusan lolos filter Holland")
        
        if filtered_majors:
            print(f"   📋 Jurusan kandidat:")
            for i, major in enumerate(filtered_majors[:5], 1):
                sim = holland_filter_result['similarity_scores'].get(major, 0)
                print(f"      {i}. {major} (similarity: {sim:.3f})")
        
        # STEP 4: Ranking menggunakan ANP
        print(f"\n🧮 Menjalankan True ANP untuk ranking final...")
        anp_results = None
        recommended_major = None
        
        try:
            if filtered_majors:
                anp_results = calculate_anp_ranking(scores, filtered_majors)
                
                if anp_results and anp_results.get('ranked_majors'):
                    recommended_major = anp_results['ranked_majors'][0][0]
                    
                    print(f"\n   ✅ Top 5 Rekomendasi ANP:")
                    for i, (major, data) in enumerate(anp_results['ranked_majors'][:5], 1):
                        print(f"      {i}. {major}: {data['anp_score']:.6f}")
                else:
                    print(f"   ⚠️ ANP tidak menghasilkan ranking")
            else:
                print(f"   ⚠️ Tidak ada jurusan yang lolos filter Holland")
            
        except Exception as e:
            print(f"   ⚠️ Error ANP: {e}")
            import traceback
            traceback.print_exc()
        
        # Fallback: gunakan Holland similarity tertinggi
        if not recommended_major and filtered_majors:
            recommended_major = filtered_majors[0]
            print(f"   ⚠️ Menggunakan fallback (Holland top-1): {recommended_major}")
        
        # STEP 5: Simpan hasil dengan data yang konsisten
        print(f"\n💾 Menyimpan hasil ke database...")
        self.save_test_result(
            student_id, 
            scores, 
            holland_code,
            top_3_types, 
            recommended_major, 
            anp_results,
            holland_filter_result,
            sorted_all_scores  # Tambahkan ini untuk konsistensi
        )
        
        print(f"✅ Proses selesai!")
        print(f"🎓 Rekomendasi final: {recommended_major}")
        print(f"{'='*60}\n")
        
        return {
            'scores': scores,
            'sorted_scores': sorted_all_scores,  # Tambahkan ini
            'holland_code': holland_code,
            'top_3_types': top_3_types,
            'recommended_major': recommended_major,
            'holland_filter': holland_filter_result,
            'anp_results': anp_results
        }