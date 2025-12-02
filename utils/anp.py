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
        self.criteria_weights = np.array([1/6] * 6)
        self.db = DatabaseManager()

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
        return np.abs(priority_vector)

    def build_supermatrix(self, riasec_scores, major_weights):
        """Bangun supermatrix ANP"""
        criteria_names = self.riasec_types
        alternative_names = list(major_weights.keys())

        n_criteria = len(criteria_names)
        n_alternatives = len(alternative_names)
        matrix_size = n_criteria + n_alternatives
        supermatrix = np.zeros((matrix_size, matrix_size))

        # Hubungan antar kriteria (independen)
        criteria_matrix = np.eye(n_criteria) * self.criteria_weights.reshape(-1, 1)
        supermatrix[0:n_criteria, 0:n_criteria] = criteria_matrix

        # Hubungan alternatif terhadap kriteria (disesuaikan dengan skor siswa)
        for i, major in enumerate(alternative_names):
            for j, criterion in enumerate(criteria_names):
                # Bobot = profil jurusan × kekuatan siswa di kriteria tersebut
                major_profile_weight = major_weights[major][criterion]
                student_strength = riasec_scores.get(criterion, 0)
                
                # Interaksi antara kebutuhan jurusan dan kemampuan siswa
                interaction_weight = major_profile_weight * student_strength
                supermatrix[n_criteria + i, j] = interaction_weight

        # Normalisasi kolom
        for j in range(matrix_size):
            col_sum = np.sum(supermatrix[:, j])
            if col_sum > 0:
                supermatrix[:, j] = supermatrix[:, j] / col_sum

        return supermatrix, criteria_names, alternative_names

    def limit_supermatrix(self, supermatrix, max_iterations=100, tolerance=1e-6):
        """Hitung limit supermatrix hingga konvergen"""
        matrix = supermatrix.copy()
        for _ in range(max_iterations):
            prev = matrix.copy()
            matrix = np.dot(matrix, matrix)
            if np.allclose(matrix, prev, atol=tolerance):
                break
        return matrix

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

        # Bangun dan proses supermatrix
        supermatrix, criteria_names, alternative_names = self.build_supermatrix(riasec_scores, major_map)
        limit_matrix = self.limit_supermatrix(supermatrix)

        n_criteria = len(criteria_names)
        alternative_priorities = limit_matrix[n_criteria:, 0]

        # Compile hasil
        major_scores = {}
        for i, major in enumerate(alternative_names):
            major_scores[major] = {
                'anp_score': float(alternative_priorities[i]),
                'riasec_profile': major_map[major],
                'criteria_weights': {
                    criterion: riasec_scores.get(criterion, 0) * major_map[major][criterion]
                    for criterion in self.riasec_types
                }
            }

        # Urutkan berdasarkan ANP score
        ranked = sorted(major_scores.items(), key=lambda x: x[1]['anp_score'], reverse=True)

        return {
            'ranked_majors': ranked,
            'total_analyzed': len(ranked),
            'student_profile': riasec_scores,
            'methodology': 'ANP (Analytic Network Process)'
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