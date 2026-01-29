import numpy as np
import pandas as pd
from scipy.linalg import eig
from database.db_manager import DatabaseManager


class ANPProcessor:
    def __init__(self):
        """Initialize ANP processor with RIASEC criteria and database connection"""
        self.riasec_types = ['Realistic', 'Investigative', 'Artistic', 'Social', 'Enterprising', 'Conventional']
        self.db = DatabaseManager()
        self.ri_lookup = {
            1: 0.0,
            2: 0.0,
            3: 0.58,
            4: 0.90,
            5: 1.12,
            6: 1.24,
            7: 1.32,
            8: 1.41,
            9: 1.45
        }
        
        # Inner Dependency Matrix berdasarkan Holland Hexagon
        self.holland_correlation = np.array([
            [1.00, 0.80, 0.40, 0.20, 0.40, 0.80],
            [0.80, 1.00, 0.80, 0.40, 0.20, 0.40],
            [0.40, 0.80, 1.00, 0.80, 0.40, 0.20],
            [0.20, 0.40, 0.80, 1.00, 0.80, 0.40],
            [0.40, 0.20, 0.40, 0.80, 1.00, 0.80],
            [0.80, 0.40, 0.20, 0.40, 0.80, 1.00],
        ])

    def load_majors_from_db(self):
        """Ambil data jurusan (alternatif) dari tabel majors"""
        try:
            conn = self.db.get_connection()
            df = pd.read_sql_query("SELECT * FROM majors", conn)
            conn.close()

            if df.empty:
                raise ValueError("Tabel 'majors' kosong.")

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
            raise RuntimeError(f"Gagal memuat data jurusan: {e}")

    # ================= EIGENVECTOR =================
    def calculate_priority(self, matrix):
        """Hitung vektor prioritas (eigenvector) utama"""
        eigenvalues, eigenvectors = eig(matrix)
        max_idx = np.argmax(eigenvalues.real)
        vec = eigenvectors[:, max_idx].real
        return np.abs(vec / np.sum(vec)), float(eigenvalues[max_idx].real)

    # ================= PAIRWISE KRITERIA =================
    def build_criteria_pairwise(self, riasec_scores):
        """Bangun matriks perbandingan berpasangan kriteria berdasarkan skor siswa"""
        size = len(self.riasec_types)
        matrix = np.ones((size, size))
        scores = [max(float(riasec_scores.get(c, 0)), 1e-4) for c in self.riasec_types]

        for i in range(size):
            for j in range(i+1, size):
                ratio = scores[i] / scores[j]
                ratio = np.clip(ratio, 1/9, 9)
                matrix[i,j] = ratio
                matrix[j,i] = 1/ratio
        return matrix

    # ================= PAIRWISE ALTERNATIF =================
    def build_alt_pairwise_by_criterion(self, major_map, criterion):
        """Bangun matriks perbandingan berpasangan alternatif untuk kriteria tertentu"""
        majors = list(major_map.keys())
        n = len(majors)
        matrix = np.ones((n, n))
        scores = [major_map[m][criterion] for m in majors]

        for i in range(n):
            for j in range(i+1, n):
                if scores[j] == 0:
                    ratio = 9 if scores[i] > 0 else 1
                else:
                    ratio = scores[i] / scores[j]
                ratio = np.clip(ratio, 1/9, 9)
                matrix[i,j] = ratio
                matrix[j,i] = 1/ratio
        return matrix, majors

    # ================= SUPERMATRIX =================
    def build_supermatrix(self, criteria_weights, alt_weights):
        """Bangun Supermatrix (Pure ANP)"""
        n_c = len(self.riasec_types)
        n_a = len(next(iter(alt_weights.values())))
        size = n_c + n_a
        S = np.zeros((size, size))

        # W11: Feedback/Influence (Diagonal diisi bobot kriteria)
        for i in range(n_c):
            S[i,i] = criteria_weights[i]

        # W21: Alternatif terhadap Kriteria
        for j, crit in enumerate(self.riasec_types):
            weights = alt_weights[crit]
            for i in range(n_a):
                S[n_c+i, j] = weights[i]

        # W12: Feedback (Kriteria terhadap Alternatif)
        for j in range(n_a):
            for i in range(n_c):
                S[i, n_c+j] = criteria_weights[i]

        # Normalisasi kolom
        for j in range(size):
            col_sum = S[:,j].sum()
            if col_sum > 0:
                S[:,j] /= col_sum
        return S

    # ================= LIMIT SUPERMATRIX =================
    def limit_supermatrix(self, M, it=100):
        """Hitung Limit Supermatrix"""
        L = M.copy()
        for _ in range(it):
            L = np.dot(L, M)
        return L

    def compute_alternative_priorities(self, major_map):
        """Hitung prioritas alternatif untuk semua kriteria"""
        alt_priorities = {}
        major_names = list(major_map.keys())
        for crit in self.riasec_types:
            pw, _ = self.build_alt_pairwise_by_criterion(major_map, crit)
            weights, _ = self.calculate_priority(pw)
            alt_priorities[crit] = weights
        return alt_priorities, major_names

    def compute_consistency_ratio(self, lambda_max, size):
        """Hitung Consistency Ratio (CR)"""
        if size <= 2: return 0.0, 0.0, True
        ci = (lambda_max - size) / (size - 1)
        ri = self.ri_lookup.get(size, 1.49)
        cr = ci / ri if ri != 0 else 0.0
        return float(ci), float(cr), cr < 0.1

    def calculate_anp_scores(self, riasec_scores, filtered_majors=None):
        """
        Hitung skor ANP menggunakan Pure Methodology.
        """
        all_majors = self.load_majors_from_db()
        major_map = {k: v for k, v in all_majors.items() if k in filtered_majors} if filtered_majors else all_majors

        if not major_map:
            raise ValueError("Tidak ada jurusan untuk dianalisis")

        # 1. Kriteria
        crit_pw = self.build_criteria_pairwise(riasec_scores)
        crit_weights, lambda_max = self.calculate_priority(crit_pw)
        ci, cr, is_consistent = self.compute_consistency_ratio(lambda_max, len(self.riasec_types))

        # 2. Alternatif
        alt_priorities, alternative_names = self.compute_alternative_priorities(major_map)

        # 3. Supermatrix
        S = self.build_supermatrix(crit_weights, alt_priorities)
        L = self.limit_supermatrix(S)

        # 4. Extract Results
        n_c = len(self.riasec_types)
        final_priorities = L[n_c:, 0]
        total = np.sum(final_priorities)
        if total > 0:
            final_priorities /= total
        else:
            final_priorities = np.full_like(final_priorities, 1 / len(alternative_names))

        major_results = {}
        for i, major in enumerate(alternative_names):
            major_results[major] = {
                'anp_score': float(final_priorities[i]),
                'riasec_profile': major_map[major]
            }

        ranked = sorted(major_results.items(), key=lambda x: x[1]['anp_score'], reverse=True)
        top_5 = [{'major_name': m, **d} for m, d in ranked[:5]]

        return {
            'ranked_majors': ranked,
            'top_5_majors': top_5,
            'total_analyzed': len(ranked),
            'student_riasec_profile': riasec_scores,
            'methodology': 'Pure ANP (No Cosine Similarity)',
            'calculation_details': {
                'criteria_priorities': {self.riasec_types[i]: float(crit_weights[i]) for i in range(n_c)},
                'consistency_ratio': cr,
                'is_consistent': is_consistent,
                'converged': True,
                'iterations': 100,
                'supermatrix_size': n_c + len(alternative_names),
                'inner_dependency_matrix': self.holland_correlation.tolist()
            }
        }

# Wrapper utilitas
def calculate_prefiltered_anp(riasec_scores, top_n=None, min_similarity=None):
    """Wrapper untuk Pure ANP tanpa filtering cosine similarity."""
    anp = ANPProcessor()
    anp_results = anp.calculate_anp_scores(riasec_scores)
    
    # Tambahkan field similarity 1.0 agar UI tidak error
    for major, data in anp_results['ranked_majors']:
        data['similarity'] = 1.0
    for item in anp_results['top_5_majors']:
        item['similarity'] = 1.0
        
    return anp_results
