"""
ANP (Analytic Network Process) Module for Decision Support System
Uses Holland Code as pre-filtering criteria before ANP ranking
"""

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

    # =======================
    # LOAD DATA DARI DATABASE
    # =======================
    def load_majors_from_db(self):
        """Ambil data jurusan (alternatif) dari tabel majors"""
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
    # PERHITUNGAN ANP
    # =======================
    def calculate_priority(self, matrix):
        """Hitung vektor prioritas menggunakan metode eigenvalue"""
        eigenvalues, eigenvectors = eig(matrix)
        max_idx = np.argmax(eigenvalues.real)
        principal_eigenvector = eigenvectors[:, max_idx].real
        priority_vector = principal_eigenvector / np.sum(principal_eigenvector)
        return np.abs(priority_vector), float(eigenvalues[max_idx].real)

    def build_pairwise_matrix(self, riasec_scores):
        """Bangun matriks perbandingan berpasangan dari skor RIASEC siswa"""
        size = len(self.riasec_types)
        matrix = np.ones((size, size))

        safe_scores = {
            t: max(float(riasec_scores.get(t, 0.0)), 1e-4)
            for t in self.riasec_types
        }

        for i in range(size):
            for j in range(i + 1, size):
                ratio = safe_scores[self.riasec_types[i]] / safe_scores[self.riasec_types[j]]
                ratio = float(np.clip(ratio, 1/9, 9))
                matrix[i, j] = ratio
                matrix[j, i] = 1 / ratio

        np.fill_diagonal(matrix, 1.0)
        return matrix

    def normalize_columns(self, matrix):
        """Normalisasi setiap kolom agar jumlahnya = 1"""
        normalized = matrix.astype(float)
        for j in range(normalized.shape[1]):
            col_sum = normalized[:, j].sum()
            if col_sum > 0:
                normalized[:, j] /= col_sum
            else:
                normalized[:, j] = 1.0 / normalized.shape[0]
        return normalized

    def compute_consistency_ratio(self, lambda_max, size):
        if size <= 2:
            return 0.0, 0.0, True

        ci = (lambda_max - size) / (size - 1)
        ri = self.ri_lookup.get(size, 1.49)
        if ri == 0:
            return float(ci), 0.0, True
        cr = ci / ri
        return float(ci), float(cr), cr < 0.1

    def build_supermatrix(self, riasec_scores, major_weights, criteria_block, criteria_priorities):
        """Bangun supermatrix ANP"""
        criteria_names = self.riasec_types
        alternative_names = list(major_weights.keys())

        n_criteria = len(criteria_names)
        n_alternatives = len(alternative_names)
        matrix_size = n_criteria + n_alternatives
        supermatrix = np.zeros((matrix_size, matrix_size))

        # Hubungan antar kriteria berdasarkan pairwise comparison
        supermatrix[0:n_criteria, 0:n_criteria] = criteria_block

        # Hubungan alternatif terhadap kriteria (disesuaikan dengan skor siswa)
        for i, major in enumerate(alternative_names):
            for j, criterion in enumerate(criteria_names):
                # Bobot = profil jurusan × kekuatan siswa di kriteria tersebut
                major_profile_weight = major_weights[major][criterion]
                student_strength = riasec_scores.get(criterion, 0)
                
                # Interaksi antara kebutuhan jurusan dan kemampuan siswa
                interaction_weight = major_profile_weight * student_strength
                supermatrix[n_criteria + i, j] = interaction_weight

        # Hubungan kriteria terhadap alternatif (feedback loop)
        for j, major in enumerate(alternative_names):
            for i, criterion in enumerate(criteria_names):
                crit_weight = criteria_priorities[i] * major_weights[major][criterion]
                supermatrix[i, n_criteria + j] = crit_weight

        # Normalisasi kolom
        for j in range(matrix_size):
            col_sum = np.sum(supermatrix[:, j])
            if col_sum > 0:
                supermatrix[:, j] = supermatrix[:, j] / col_sum
            else:
                supermatrix[:, j] = 1.0 / matrix_size

        return supermatrix, criteria_names, alternative_names

    def limit_supermatrix(self, supermatrix, max_iterations=100, tolerance=1e-6):
        """Hitung limit supermatrix hingga konvergen"""
        matrix = supermatrix.copy()
        for iteration in range(1, max_iterations + 1):
            next_matrix = np.dot(matrix, supermatrix)
            for j in range(next_matrix.shape[1]):
                col_sum = np.sum(next_matrix[:, j])
                if col_sum > 0:
                    next_matrix[:, j] /= col_sum
                else:
                    next_matrix[:, j] = 1.0 / next_matrix.shape[0]

            if np.allclose(next_matrix, matrix, atol=tolerance):
                return next_matrix, iteration, True
            matrix = next_matrix

        return matrix, max_iterations, False

    def calculate_anp_scores(self, riasec_scores, filtered_majors=None):
        """
        Hitung skor ANP untuk jurusan
        
        Args:
            riasec_scores: Normalized RIASEC scores dari siswa (dict)
            filtered_majors: List nama jurusan yang sudah difilter (optional)
        
        Returns:
            Dictionary berisi ranking jurusan dengan skor ANP
        """
        # Ambil data jurusan dari database
        all_majors = self.load_majors_from_db()
        
        # Filter jurusan jika ada
        if filtered_majors:
            major_map = {k: v for k, v in all_majors.items() if k in filtered_majors}
        else:
            major_map = all_majors

        if not major_map:
            raise ValueError("Tidak ada jurusan yang tersedia untuk dianalisis")

        # Pairwise comparison dan bobot kriteria
        pairwise_matrix = self.build_pairwise_matrix(riasec_scores)
        criteria_priorities, lambda_max = self.calculate_priority(pairwise_matrix)
        ci, cr, is_consistent = self.compute_consistency_ratio(lambda_max, len(self.riasec_types))
        criteria_block = self.normalize_columns(pairwise_matrix)

        # Bangun dan proses supermatrix
        supermatrix, criteria_names, alternative_names = self.build_supermatrix(
            riasec_scores,
            major_map,
            criteria_block,
            criteria_priorities
        )
        limit_matrix, iterations, converged = self.limit_supermatrix(supermatrix)

        n_criteria = len(criteria_names)
        alternative_block = limit_matrix[n_criteria:, :n_criteria]
        if alternative_block.size == 0:
            raise ValueError("Limit supermatrix tidak memiliki blok alternatif yang valid")

        alternative_priorities = alternative_block.mean(axis=1)
        total_priority = np.sum(alternative_priorities)
        if total_priority > 0:
            alternative_priorities = alternative_priorities / total_priority
        else:
            alternative_priorities = np.full_like(alternative_priorities, 1 / len(alternative_priorities))

        # Compile hasil
        major_scores = {}
        for i, major in enumerate(alternative_names):
            contribution = {
                criterion: float(criteria_priorities[idx] * major_map[major][criterion] * riasec_scores.get(criterion, 0))
                for idx, criterion in enumerate(self.riasec_types)
            }
            major_scores[major] = {
                'anp_score': float(alternative_priorities[i]),
                'riasec_profile': major_map[major],
                'criteria_weights': contribution
            }

        # Urutkan berdasarkan ANP score
        ranked = sorted(major_scores.items(), key=lambda x: x[1]['anp_score'], reverse=True)
        top_5 = [
            {
                'major_name': major,
                **data
            }
            for major, data in ranked[:5]
        ]

        return {
            'ranked_majors': ranked,
            'total_analyzed': len(ranked),
            'student_riasec_profile': riasec_scores,
            'methodology': 'ANP (Analytic Network Process)',
            'top_5_majors': top_5,
            'calculation_details': {
                'pairwise_matrix': pairwise_matrix.tolist(),
                'criteria_priorities': {
                    criterion: float(criteria_priorities[idx])
                    for idx, criterion in enumerate(criteria_names)
                },
                'consistency_index': ci,
                'consistency_ratio': cr,
                'is_consistent': is_consistent,
                'iterations': iterations,
                'converged': converged,
                'supermatrix_size': len(criteria_names) + len(alternative_names)
            }
        }


# Fungsi utilitas
def calculate_anp_ranking(riasec_scores, filtered_majors=None):
    """
    Main function untuk ranking ANP
    
    Args:
        riasec_scores: Skor RIASEC siswa (normalized)
        filtered_majors: List jurusan kandidat dari Holland filtering
    """
    anp = ANPProcessor()
    return anp.calculate_anp_scores(riasec_scores, filtered_majors)


# Testing manual
if __name__ == "__main__":
    sample_scores = {
        'Realistic': 0.75,
        'Investigative': 1.00,
        'Artistic': 0.40,
        'Social': 0.60,
        'Enterprising': 0.50,
        'Conventional': 0.90
    }
    
    # Test tanpa filter
    results = calculate_anp_ranking(sample_scores)
    print("\n=== HASIL RANKING ANP (Semua Jurusan) ===")
    for i, (major, data) in enumerate(results['ranked_majors'][:5], 1):
        print(f"{i}. {major}: {data['anp_score']:.4f}")
    
    # Test dengan filter
    filtered = ['Teknik Informatika', 'Sistem Informasi', 'Teknik Elektro']
    results_filtered = calculate_anp_ranking(sample_scores, filtered)
    print("\n=== HASIL RANKING ANP (Filtered) ===")
    for i, (major, data) in enumerate(results_filtered['ranked_majors'], 1):
        print(f"{i}. {major}: {data['anp_score']:.4f}")