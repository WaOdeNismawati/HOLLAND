import numpy as np
import pandas as pd
from scipy.linalg import eig
from database.db_manager import DatabaseManager


class ANPProcessor:
    def __init__(self):
        """Inisialisasi ANP dengan 6 dimensi RIASEC dan koneksi database"""
        self.riasec_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
        self.db = DatabaseManager()
        
        # Holland Hexagon Model - Define adjacent relationships
        # Tipe yang adjacent (bersebelahan) di hexagon Holland memiliki korelasi lebih kuat
        self.holland_adjacency = {
            'Realistic': ['Investigative', 'Conventional'],
            'Investigative': ['Realistic', 'Artistic'],
            'Artistic': ['Investigative', 'Social'],
            'Social': ['Artistic', 'Enterprising'],
            'Enterprising': ['Social', 'Conventional'],
            'Conventional': ['Enterprising', 'Realistic']
        }

    # =======================
    # LOAD DATA JURUSAN
    # =======================
    def load_majors_from_db(self):
        """Ambil data jurusan dari tabel 'majors' dan ubah jadi dict"""
        try:
            conn = self.db.get_connection()
            df = pd.read_sql_query("SELECT * FROM majors", conn)
            conn.close()

            if df.empty:
                raise ValueError("Tabel 'majors' kosong. Silakan unggah data CSV jurusan terlebih dahulu.")

            major_map = {}
            for _, row in df.iterrows():
                major_map[row['Major']] = {
                    'Realistic': float(row['Realistic']),
                    'Investigative': float(row['Investigative']),
                    'Artistic': float(row['Artistic']),
                    'Social': float(row['Social']),
                    'Enterprising': float(row['Enterprising']),
                    'Conventional': float(row['Conventional'])
                }
            return major_map
        except Exception as e:
            raise RuntimeError(f"Gagal memuat data jurusan dari database: {e}")

    # =======================
    # INTERDEPENDENCY MATRIX (TRUE ANP!)
    # =======================
    def build_interdependency_matrix(self, riasec_scores):
        """
        Buat matriks interdependensi antar kriteria RIASEC
        berdasarkan Holland Hexagon Model
        
        Ini adalah perbedaan UTAMA antara AHP dan ANP!
        
        Teori Holland: Tipe kepribadian yang adjacent (bersebelahan) di hexagon
        memiliki hubungan yang lebih kuat dibanding yang opposite.
        
        Bobot interdependensi:
        - Self (diagonal): 50% - pengaruh diri sendiri paling kuat
        - Adjacent: 30% - tipe bersebelahan di hexagon
        - Opposite: 20% - tipe berseberang di hexagon
        """
        n = len(self.riasec_types)
        interdependency = np.zeros((n, n))
        
        print(f"\n🔗 Membangun Interdependency Matrix (Holland Hexagon Model)")
        
        for i, type_i in enumerate(self.riasec_types):
            for j, type_j in enumerate(self.riasec_types):
                if i == j:
                    # Self-dependency: paling kuat (50%)
                    weight = 0.50
                    interdependency[i, j] = riasec_scores[type_i] * weight
                elif type_j in self.holland_adjacency[type_i]:
                    # Adjacent type: sedang (30%)
                    weight = 0.30
                    interdependency[i, j] = riasec_scores[type_i] * weight
                else:
                    # Opposite type: lemah (20%)
                    weight = 0.20
                    interdependency[i, j] = riasec_scores[type_i] * weight
        
        # Normalisasi per kolom (stochastic matrix)
        for j in range(n):
            col_sum = np.sum(interdependency[:, j])
            if col_sum > 0:
                interdependency[:, j] = interdependency[:, j] / col_sum
        
        print(f"   ✓ Interdependency matrix berhasil dibuat")
        print(f"   ✓ Matrix menggambarkan hubungan antar tipe RIASEC")
        
        return interdependency

    # =======================
    # PAIRWISE COMPARISON MATRIX
    # =======================
    def create_pairwise_matrix(self, riasec_scores):
        """
        Buat matriks perbandingan berpasangan antar kriteria RIASEC
        Menggunakan intensitas Saaty scale (1-9)
        """
        n = len(self.riasec_types)
        matrix = np.ones((n, n))
        
        scores = [riasec_scores[t] for t in self.riasec_types]
        
        for i in range(n):
            for j in range(i+1, n):
                if scores[i] == 0 and scores[j] == 0:
                    ratio = 1
                elif scores[j] == 0:
                    ratio = 9
                elif scores[i] == 0:
                    ratio = 1/9
                else:
                    ratio = scores[i] / scores[j]
                
                # Scale to Saaty's 1-9 scale
                if ratio >= 1:
                    matrix[i, j] = min(9, 1 + (ratio - 1) * 8)
                else:
                    matrix[i, j] = max(1/9, 1 / (1 + (1/ratio - 1) * 8))
                
                matrix[j, i] = 1 / matrix[i, j]
        
        return matrix

    # =======================
    # HITUNG VEKTOR PRIORITAS
    # =======================
    def calculate_priority_vector(self, matrix):
        """
        Hitung vektor prioritas dengan metode eigenvalue (principal eigenvector)
        """
        try:
            eigenvalues, eigenvectors = eig(matrix)
            max_idx = np.argmax(eigenvalues.real)
            principal_eigenvector = eigenvectors[:, max_idx].real
            priority_vector = principal_eigenvector / np.sum(principal_eigenvector)
            return np.abs(priority_vector)
        except Exception as e:
            print(f"Warning: Error calculating priority - {e}")
            # Return uniform distribution as fallback
            n = len(matrix)
            return np.ones(n) / n

    # =======================
    # HITUNG CONSISTENCY RATIO
    # =======================
    def calculate_consistency_ratio(self, matrix, priority_vector):
        """
        Hitung Consistency Ratio (CR) untuk validasi
        CR < 0.1 dianggap konsisten
        """
        n = len(matrix)
        
        # Random Index (RI) values for n=1 to 10
        RI = [0, 0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]
        
        if n < 2 or n > 10:
            return 0
        
        # Calculate λmax (maximum eigenvalue)
        weighted_sum = np.dot(matrix, priority_vector)
        lambda_max = np.mean(weighted_sum / priority_vector)
        
        # Calculate Consistency Index (CI)
        CI = (lambda_max - n) / (n - 1)
        
        # Calculate Consistency Ratio (CR)
        CR = CI / RI[n-1] if n > 1 else 0
        
        return CR

    # =======================
    # BANGUN SUPERMATRIX ANP (TRUE ANP!)
    # =======================
    def build_unweighted_supermatrix(self, riasec_scores, major_weights, criteria_priorities):
        """
        Bangun unweighted supermatrix dengan INTERDEPENDENSI kriteria (True ANP!)
        
        Struktur Supermatrix:
        ┌─────────────────────────────┬──────────────────┐
        │ Blok (1,1):                 │ Blok (1,2):      │
        │ Kriteria × Kriteria         │ Alt → Kriteria   │
        │ INTERDEPENDENCY MATRIX ✓    │ (biasanya 0)     │
        ├─────────────────────────────┼──────────────────┤
        │ Blok (2,1):                 │ Blok (2,2):      │
        │ Kriteria → Alternatif       │ Alt × Alt        │
        │ (pengaruh kriteria ke jur)  │ (biasanya 0)     │
        └─────────────────────────────┴──────────────────┘
        
        PERBEDAAN UTAMA dengan Pseudo-ANP:
        - Blok (1,1) BUKAN identity matrix
        - Blok (1,1) = Interdependency matrix berdasarkan Holland Hexagon
        - Ini memungkinkan network effect antar kriteria RIASEC
        """
        criteria_names = self.riasec_types
        alternative_names = list(major_weights.keys())

        n_criteria = len(criteria_names)
        n_alternatives = len(alternative_names)
        matrix_size = n_criteria + n_alternatives
        
        supermatrix = np.zeros((matrix_size, matrix_size))

        # Blok (1,1): Interdependensi kriteria (INI YANG MEMBEDAKAN ANP dari AHP!)
        print(f"\n🏗️  Blok (1,1): Interdependensi Kriteria RIASEC")
        criteria_interdependency = self.build_interdependency_matrix(riasec_scores)
        supermatrix[0:n_criteria, 0:n_criteria] = criteria_interdependency
        
        print(f"\n   Contoh hubungan interdependensi:")
        print(f"   - Realistic → Realistic: {criteria_interdependency[0,0]:.3f} (self)")
        print(f"   - Realistic → Investigative: {criteria_interdependency[0,1]:.3f} (adjacent)")
        print(f"   - Realistic → Artistic: {criteria_interdependency[0,2]:.3f} (opposite)")

        # Blok (2,1): Pengaruh kriteria terhadap alternatif
        print(f"\n📊 Blok (2,1): Pengaruh Kriteria → Alternatif")
        for i, major in enumerate(alternative_names):
            for j, criterion in enumerate(criteria_names):
                # Skor jurusan pada kriteria ini
                major_score = major_weights[major][criterion]
                # Bobot kriteria dari profil siswa
                criterion_weight = criteria_priorities[j]
                # Kombinasi: seberapa relevan jurusan ini untuk kriteria ini
                supermatrix[n_criteria + i, j] = major_score * criterion_weight

        # Normalisasi setiap kolom (stochastic matrix)
        print(f"\n⚖️  Normalisasi kolom supermatrix...")
        for j in range(matrix_size):
            col_sum = np.sum(supermatrix[:, j])
            if col_sum > 0:
                supermatrix[:, j] = supermatrix[:, j] / col_sum

        print(f"   ✓ Unweighted Supermatrix berhasil dibuat ({matrix_size}×{matrix_size})")
        
        return supermatrix, criteria_names, alternative_names

    # =======================
    # WEIGHTED SUPERMATRIX
    # =======================
    def create_weighted_supermatrix(self, unweighted_supermatrix, criteria_priorities):
        """
        Buat weighted supermatrix dengan membobot blok berdasarkan prioritas kriteria
        """
        n_criteria = len(criteria_priorities)
        weighted = unweighted_supermatrix.copy()
        
        # Bobot blok kriteria (kolom 0 hingga n_criteria-1)
        for j in range(n_criteria):
            weighted[:, j] = weighted[:, j] * criteria_priorities[j]
        
        # Normalisasi ulang per kolom
        for j in range(weighted.shape[1]):
            col_sum = np.sum(weighted[:, j])
            if col_sum > 0:
                weighted[:, j] = weighted[:, j] / col_sum
        
        return weighted

    # =======================
    # LIMIT SUPERMATRIX
    # =======================
    def limit_supermatrix(self, weighted_supermatrix, max_iterations=200, tolerance=1e-8):
        """Iterasikan weighted supermatrix hingga mencapai kondisi steady-state."""
        matrix = weighted_supermatrix.copy()
        prev = np.zeros_like(matrix)
        iteration = 0
        converged = False

        while iteration < max_iterations:
            if np.allclose(matrix, prev, atol=tolerance):
                converged = True
                print(f"   ✓ Konvergen pada iterasi {iteration}")
                break

            prev = matrix.copy()
            matrix = np.dot(matrix, weighted_supermatrix)
            iteration += 1

        if not converged:
            print(f"   ⚠ Tidak konvergen setelah {max_iterations} iterasi")

        return matrix, converged, iteration

    # =======================
    # HITUNG SKOR ANP
    # =======================
    def calculate_anp_scores(self, riasec_scores, filtered_majors=None):
        """
        Hitung skor ANP untuk jurusan dengan metode TRUE ANP.
        
        Tahapan ANP:
        1. Pairwise comparison antar kriteria RIASEC
        2. Hitung priority vector kriteria
        3. Build interdependency matrix (Holland Hexagon) ← TRUE ANP!
        4. Build unweighted supermatrix dengan interdependensi
        5. Create weighted supermatrix
        6. Hitung limit supermatrix
        7. Ekstrak prioritas alternatif (jurusan)
        
        Args:
            riasec_scores: dict berisi skor RIASEC siswa (sudah dinormalisasi)
            filtered_majors: list jurusan hasil filter Holland (opsional)
        Returns:
            dict hasil ranking jurusan dengan detail perhitungan
        """
        print("\n" + "="*70)
        print("🔬 PROSES PERHITUNGAN TRUE ANP (dengan Interdependensi)")
        print("="*70)
        
        # 1️⃣ Ambil semua jurusan dari DB
        all_majors = self.load_majors_from_db()

        # 2️⃣ Filter jurusan (jika ada)
        if filtered_majors:
            major_map = {k: v for k, v in all_majors.items() if k in filtered_majors}
        else:
            major_map = all_majors

        if not major_map:
            raise ValueError("Tidak ada jurusan yang tersedia untuk dianalisis.")

        print(f"\n📊 Jumlah jurusan yang dianalisis: {len(major_map)}")

        # 3️⃣ Buat pairwise comparison matrix untuk kriteria
        print("\n📐 Step 1: Pairwise Comparison Matrix")
        pairwise_matrix = self.create_pairwise_matrix(riasec_scores)
        print("   ✓ Matriks perbandingan berpasangan dibuat")
        
        # 4️⃣ Hitung priority vector kriteria
        print("\n🎯 Step 2: Priority Vector Kriteria")
        criteria_priorities = self.calculate_priority_vector(pairwise_matrix)
        
        print("   Bobot Kriteria:")
        for i, criterion in enumerate(self.riasec_types):
            print(f"   - {criterion:15s}: {criteria_priorities[i]:.4f}")
        
        # 5️⃣ Hitung Consistency Ratio
        CR = self.calculate_consistency_ratio(pairwise_matrix, criteria_priorities)
        print(f"\n   Consistency Ratio (CR): {CR:.4f}")
        if CR < 0.1:
            print("   ✓ Matriks konsisten (CR < 0.1)")
        else:
            print("   ⚠ Matriks kurang konsisten (CR ≥ 0.1)")

        # 6️⃣ Bangun unweighted supermatrix DENGAN INTERDEPENDENSI (True ANP!)
        print("\n🏗️ Step 3: Unweighted Supermatrix (dengan Interdependensi)")
        unweighted_supermatrix, criteria_names, alternative_names = \
            self.build_unweighted_supermatrix(riasec_scores, major_map, criteria_priorities)
        print(f"   ✓ Dimensi supermatrix: {unweighted_supermatrix.shape}")

        # 7️⃣ Buat weighted supermatrix
        print("\n⚖️ Step 4: Weighted Supermatrix")
        weighted_supermatrix = self.create_weighted_supermatrix(
            unweighted_supermatrix, criteria_priorities
        )
        print("   ✓ Supermatrix telah dibobotkan")

        # 8️⃣ Hitung limit supermatrix
        print("\n🔄 Step 5: Limit Supermatrix (Iterasi hingga konvergen)")
        limit_matrix, converged, iterations = self.limit_supermatrix(weighted_supermatrix)
        
        # 9️⃣ Ekstrak prioritas alternatif dengan merata-ratakan kolom kriteria
        n_criteria = len(criteria_names)
        alternative_block = limit_matrix[n_criteria:, :n_criteria]
        alternative_priorities = alternative_block.mean(axis=1)
        if np.sum(alternative_priorities) > 0:
            alternative_priorities = alternative_priorities / np.sum(alternative_priorities)
        
        print(f"\n📊 Step 6: Ekstraksi Prioritas Alternatif")
        print(f"   ✓ Prioritas {len(alternative_names)} jurusan berhasil dihitung")

        # 🔟 Simpan skor tiap jurusan dengan struktur lengkap
        major_scores = {}
        for i, major in enumerate(alternative_names):
            # Hitung kontribusi setiap kriteria
            criteria_contributions = {}
            for j, criterion in enumerate(self.riasec_types):
                contribution = (
                    criteria_priorities[j] * 
                    riasec_scores.get(criterion, 0) * 
                    major_map[major][criterion]
                )
                criteria_contributions[criterion] = float(contribution)
            
            major_scores[major] = {
                'anp_score': float(alternative_priorities[i]),
                'riasec_profile': major_map[major],
                'criteria_weights': criteria_contributions,
                'criteria_priorities': {
                    criterion: float(criteria_priorities[j])
                    for j, criterion in enumerate(self.riasec_types)
                }
            }

        # 1️⃣1️⃣ Urutkan berdasarkan skor ANP
        ranked = sorted(major_scores.items(), key=lambda x: x[1]['anp_score'], reverse=True)
        top_5 = ranked[:5] if len(ranked) >= 5 else ranked

        print(f"\n🏆 Top 5 Hasil Ranking:")
        for i, (major, data) in enumerate(top_5, 1):
            print(f"   {i}. {major}: {data['anp_score']:.6f}")

        print("\n" + "="*70)
        print("✅ PERHITUNGAN TRUE ANP SELESAI")
        print("="*70 + "\n")

        # 1️⃣2️⃣ Kembalikan hasil lengkap dengan detail perhitungan
        return {
            'ranked_majors': ranked,
            'top_5_majors': top_5,
            'total_analyzed': len(ranked),
            'student_profile': riasec_scores,
            'methodology': 'True ANP (Analytic Network Process with Interdependency)',
            'calculation_details': {
                'pairwise_matrix': pairwise_matrix.tolist(),
                'criteria_priorities': {
                    criterion: float(criteria_priorities[i])
                    for i, criterion in enumerate(self.riasec_types)
                },
                'consistency_ratio': float(CR),
                'is_consistent': bool(CR < 0.1),
                'supermatrix_size': unweighted_supermatrix.shape[0],
                'converged': converged,
                'iterations': iterations,
                'has_interdependency': True,  # Flag untuk menandai ini True ANP
                'holland_hexagon_applied': True
            }
        }


# =======================
# FUNGSI PEMBUNGKUS UTAMA
# =======================
def calculate_anp_ranking(riasec_scores, filtered_majors=None):
    """
    Fungsi utama untuk menghasilkan ranking ANP.
    Args:
        riasec_scores: Skor RIASEC siswa (normalized)
        filtered_majors: List jurusan kandidat dari Holland filtering
    """
    try:
        anp = ANPProcessor()
        return anp.calculate_anp_scores(riasec_scores, filtered_majors)
    except Exception as e:
        print(f"Error dalam calculate_anp_ranking: {e}")
        import traceback
        traceback.print_exc()
        return None


# =======================
# TESTING MANUAL
# =======================
if __name__ == "__main__":
    sample_scores = {
        'Realistic': 0.75,
        'Investigative': 1.00,
        'Artistic': 0.40,
        'Social': 0.60,
        'Enterprising': 0.50,
        'Conventional': 0.90
    }

    results = calculate_anp_ranking(sample_scores)
    if results:
        print("\n=== HASIL RANKING TRUE ANP ===")
        for i, (major, data) in enumerate(results['top_5_majors'], 1):
            print(f"{i}. {major}: {data['anp_score']:.6f}")
        
        print("\n=== DETAIL PERHITUNGAN ===")
        calc_details = results['calculation_details']
        print(f"Consistency Ratio: {calc_details['consistency_ratio']:.4f}")
        print(f"Konsisten: {'Ya' if calc_details['is_consistent'] else 'Tidak'}")
        print(f"Iterasi konvergen: {calc_details['iterations']}")
        print(f"Menggunakan Interdependensi: {'Ya' if calc_details['has_interdependency'] else 'Tidak'}")
        print(f"Holland Hexagon Model: {'Diterapkan' if calc_details['holland_hexagon_applied'] else 'Tidak'}")
    else:
        print("Gagal menghitung ranking ANP")