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
        
        # =====================================================
        # INNER DEPENDENCY MATRIX BERDASARKAN HOLLAND HEXAGON
        # =====================================================
        # Teori Holland: Tipe yang berdekatan di hexagon saling berkorelasi
        # Hexagon: R - I - A - S - E - C - R (circular)
        # 
        # Korelasi:
        #   - Adjacent (berdekatan): korelasi tinggi (0.8)
        #   - Alternate (selang 1): korelasi sedang (0.4)
        #   - Opposite (berlawanan): korelasi rendah (0.2)
        #
        # Urutan: R=0, I=1, A=2, S=3, E=4, C=5
        #
        self.holland_correlation = np.array([
            # R     I     A     S     E     C
            [1.00, 0.80, 0.40, 0.20, 0.40, 0.80],  # R: adjacent to I,C; opposite to S
            [0.80, 1.00, 0.80, 0.40, 0.20, 0.40],  # I: adjacent to R,A; opposite to E
            [0.40, 0.80, 1.00, 0.80, 0.40, 0.20],  # A: adjacent to I,S; opposite to C
            [0.20, 0.40, 0.80, 1.00, 0.80, 0.40],  # S: adjacent to A,E; opposite to R
            [0.40, 0.20, 0.40, 0.80, 1.00, 0.80],  # E: adjacent to S,C; opposite to I
            [0.80, 0.40, 0.20, 0.40, 0.80, 1.00],  # C: adjacent to E,R; opposite to A
        ])

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
    # INNER DEPENDENCY
    # =======================
    def get_inner_dependency_matrix(self):
        """
        Mengembalikan matriks inner dependency antar kriteria RIASEC.
        Berdasarkan Holland Hexagon Theory dimana tipe yang berdekatan
        memiliki hubungan yang lebih kuat.
        """
        return self.holland_correlation.copy()
    
    def build_inner_dependency_pairwise(self):
        """
        Bangun pairwise comparison matrix untuk inner dependency antar kriteria.
        Menghasilkan matriks yang TIDAK perfectly consistent sehingga CR > 0.
        """
        size = len(self.riasec_types)
        matrix = np.ones((size, size))
        
        # Konversi korelasi ke skala Saaty (1-9)
        # Korelasi tinggi (0.8) -> nilai rendah (mendekati 1, artinya setara pentingnya)
        # Korelasi rendah (0.2) -> nilai tinggi (sampai 5, artinya ada perbedaan signifikan)
        for i in range(size):
            for j in range(i + 1, size):
                correlation = self.holland_correlation[i, j]
                
                # Konversi: korelasi tinggi = perbedaan kecil, korelasi rendah = perbedaan besar
                # Formula: saaty_value = 1 + (1 - correlation) * 4
                # Hasil: 0.8 -> 1.8, 0.4 -> 3.4, 0.2 -> 4.2
                saaty_value = 1 + (1 - correlation) * 4
                
                # Tambahkan sedikit variasi untuk menghasilkan inkonsistensi yang wajar
                # Variasi berdasarkan posisi dalam hexagon
                position_factor = 1 + 0.1 * abs(i - j) / size
                saaty_value *= position_factor
                
                # Clip ke range Saaty yang valid
                saaty_value = float(np.clip(saaty_value, 1, 9))
                
                matrix[i, j] = saaty_value
                matrix[j, i] = 1 / saaty_value
        
        np.fill_diagonal(matrix, 1.0)
        return matrix

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
        """
        Bangun matriks perbandingan berpasangan dari skor RIASEC siswa
        dengan mempertimbangkan inner dependency dari Holland Hexagon.
        """
        size = len(self.riasec_types)
        matrix = np.ones((size, size))

        safe_scores = {
            t: max(float(riasec_scores.get(t, 0.0)), 1e-4)
            for t in self.riasec_types
        }

        # Dapatkan inner dependency matrix
        inner_dep = self.get_inner_dependency_matrix()

        for i in range(size):
            for j in range(i + 1, size):
                # Rasio dasar dari skor siswa
                base_ratio = safe_scores[self.riasec_types[i]] / safe_scores[self.riasec_types[j]]
                
                # Faktor korelasi dari Holland Hexagon
                # Tipe yang berkorelasi tinggi akan memiliki pengaruh yang lebih seimbang
                correlation_factor = inner_dep[i, j]
                
                # Modifikasi rasio berdasarkan korelasi:
                # - Korelasi tinggi (0.8): rasio mendekati 1 (lebih seimbang)
                # - Korelasi rendah (0.2): rasio lebih ekstrem
                # Formula: adjusted_ratio = base_ratio ^ (1 - correlation_factor * 0.5)
                if base_ratio > 1:
                    adjusted_ratio = base_ratio ** (1 - correlation_factor * 0.3)
                else:
                    adjusted_ratio = base_ratio ** (1 + correlation_factor * 0.3)
                
                # Clip ke range Saaty
                adjusted_ratio = float(np.clip(adjusted_ratio, 1/9, 9))
                
                matrix[i, j] = adjusted_ratio
                matrix[j, i] = 1 / adjusted_ratio

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

    def build_alternative_similarity_matrix(self, major_weights, alpha=0.3):
        """
        Bangun matriks cosine similarity antar alternatif (jurusan).
        
        Args:
            major_weights: Dictionary profil RIASEC setiap jurusan
            alpha: Faktor pengali (0-1) untuk mengontrol pengaruh similarity
        
        Returns:
            Matriks similarity (n_alternatives × n_alternatives)
        """
        alternative_names = list(major_weights.keys())
        n_alternatives = len(alternative_names)
        similarity_matrix = np.zeros((n_alternatives, n_alternatives))
        
        # Bangun vektor profil untuk setiap jurusan
        profiles = []
        for major in alternative_names:
            profile = major_weights[major]
            vector = np.array([profile[c] for c in self.riasec_types])
            profiles.append(vector)
        
        # Hitung cosine similarity untuk setiap pasangan
        for i in range(n_alternatives):
            for j in range(n_alternatives):
                if i == j:
                    similarity_matrix[i, j] = 1.0  # Similarity dengan diri sendiri
                else:
                    # Cosine similarity = dot(A,B) / (||A|| × ||B||)
                    dot_product = np.dot(profiles[i], profiles[j])
                    norm_i = np.linalg.norm(profiles[i])
                    norm_j = np.linalg.norm(profiles[j])
                    
                    if norm_i > 0 and norm_j > 0:
                        cos_sim = dot_product / (norm_i * norm_j)
                    else:
                        cos_sim = 0.0
                    
                    # Terapkan faktor pengali
                    similarity_matrix[i, j] = alpha * cos_sim
        
        return similarity_matrix, alternative_names

    def build_supermatrix(self, riasec_scores, major_weights, criteria_block, criteria_priorities, alpha=0.0):
        """
        Bangun supermatrix ANP dengan inner dependency (TANPA alternative similarity).
        
        Struktur Supermatrix (DIPERBAIKI):
        ┌─────────────────────────────────────────┐
        │  [Kriteria×Kriteria]  [Kriteria×Alt]    │
        │  W₁₁ (inner dep)      W₁₂ (feedback)    │
        │                                         │
        │  [Alternatif×Krit]    [0]               │
        │  W₂₁ (pengaruh)       W₂₂ = 0           │
        └─────────────────────────────────────────┘
        
        PERBAIKAN: W₂₂ diset ke 0 untuk menghindari averaging effect
        yang menyebabkan skor jurusan menjadi seragam.
        
        Args:
            riasec_scores: Skor RIASEC siswa (normalized)
            major_weights: Profil RIASEC setiap jurusan
            criteria_block: Matriks kriteria yang sudah dinormalisasi
            criteria_priorities: Bobot prioritas kriteria
            alpha: Tidak digunakan (kept for backward compatibility)
        """
        criteria_names = self.riasec_types
        alternative_names = list(major_weights.keys())

        n_criteria = len(criteria_names)
        n_alternatives = len(alternative_names)
        matrix_size = n_criteria + n_alternatives
        supermatrix = np.zeros((matrix_size, matrix_size))

        # =====================================================
        # BLOK W₁₁: KRITERIA × KRITERIA (Inner Dependency)
        # =====================================================
        inner_dep = self.get_inner_dependency_matrix()
        
        for i in range(n_criteria):
            for j in range(n_criteria):
                if i == j:
                    supermatrix[i, j] = criteria_block[i, j]
                else:
                    influence = criteria_block[i, j] * inner_dep[i, j]
                    supermatrix[i, j] = influence

        # =====================================================
        # BLOK W₂₁: ALTERNATIF × KRITERIA (Pengaruh Utama)
        # =====================================================
        # Ini adalah blok terpenting: seberapa cocok jurusan dengan kriteria siswa
        for i, major in enumerate(alternative_names):
            for j, criterion in enumerate(criteria_names):
                major_profile_weight = major_weights[major][criterion]
                student_strength = riasec_scores.get(criterion, 0)
                # Interaksi: jurusan cocok jika profil jurusan AND kekuatan siswa sama-sama tinggi
                interaction_weight = major_profile_weight * student_strength
                supermatrix[n_criteria + i, j] = interaction_weight

        # =====================================================
        # BLOK W₁₂: KRITERIA × ALTERNATIF (Feedback Loop)
        # =====================================================
        for j, major in enumerate(alternative_names):
            for i, criterion in enumerate(criteria_names):
                crit_weight = criteria_priorities[i] * major_weights[major][criterion]
                supermatrix[i, n_criteria + j] = crit_weight

        # =====================================================
        # BLOK W₂₂: ALTERNATIF × ALTERNATIF
        # PERBAIKAN: Set ke 0 (tidak ada hubungan antar alternatif)
        # Ini mencegah averaging effect yang membuat skor seragam
        # =====================================================
        # supermatrix[n_criteria:, n_criteria:] = 0 (sudah 0 dari np.zeros)

        # =====================================================
        # NORMALISASI KOLOM
        # =====================================================
        for j in range(matrix_size):
            col_sum = np.sum(supermatrix[:, j])
            if col_sum > 0:
                supermatrix[:, j] = supermatrix[:, j] / col_sum
            else:
                # Untuk kolom alternatif-alternatif yang 0, biarkan 0
                # Ini akan diabaikan saat ekstraksi prioritas
                pass

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
        n_alternatives = len(alternative_names)
        
        # =====================================================
        # PERBAIKAN: Ekstraksi prioritas HANYA dari kolom kriteria
        # Ini menghasilkan skor yang lebih diferensiatif karena:
        # 1. Tidak terpengaruh oleh W₂₂ (yang sudah 0)
        # 2. Fokus pada hubungan alternatif-kriteria
        # =====================================================
        
        # Ambil blok alternatif × kriteria saja (bukan semua kolom)
        alternative_block = limit_matrix[n_criteria:, :n_criteria]
        
        if alternative_block.size == 0:
            raise ValueError("Limit supermatrix tidak memiliki blok alternatif yang valid")

        # Weighted sum menggunakan criteria priorities
        # Score = Σ(alternative_block[i,j] × criteria_priorities[j])
        alternative_priorities = np.dot(alternative_block, criteria_priorities)
        
        # Normalisasi agar total = 1
        total_priority = np.sum(alternative_priorities)
        if total_priority > 0:
            alternative_priorities = alternative_priorities / total_priority
        else:
            alternative_priorities = np.full_like(alternative_priorities, 1 / n_alternatives)

        # Compile hasil
        major_scores = {}
        for i, major in enumerate(alternative_names):
            # Kontribusi per kriteria untuk analisis detail
            contribution = {
                criterion: float(alternative_block[i, idx] * criteria_priorities[idx])
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
            'methodology': 'ANP dengan Inner Dependency (Diperbaiki)',
            'top_5_majors': top_5,
            'calculation_details': {
                'pairwise_matrix': pairwise_matrix.tolist(),
                'criteria_priorities': {
                    criterion: float(criteria_priorities[idx])
                    for idx, criterion in enumerate(criteria_names)
                },
                'inner_dependency_matrix': self.holland_correlation.tolist(),
                'consistency_index': ci,
                'consistency_ratio': cr,
                'is_consistent': is_consistent,
                'iterations': iterations,
                'converged': converged,
                'supermatrix_size': n_criteria + n_alternatives,
                'extraction_method': 'Weighted sum dari blok alternatif×kriteria dengan criteria priorities',
                'inner_dependency_note': 'Based on Holland Hexagon Theory: Adjacent types have high correlation (0.8), opposite types have low correlation (0.2)'
            }
        }




# Fungsi utilitas utama
def calculate_prefiltered_anp(riasec_scores, top_n=25, min_similarity=0.5):
    """
    PRE-FILTERING + PURE ANP (RECOMMENDED)
    
    Alur:
    1. Hitung Cosine Similarity untuk SEMUA jurusan
    2. Filter: ambil top_n jurusan dengan similarity >= min_similarity
    3. Jalankan Pure ANP hanya pada jurusan yang lolos filter
    4. Return ranking final dengan info similarity
    
    Args:
        riasec_scores: Normalized RIASEC scores dari siswa (dict)
        top_n: Jumlah maksimal jurusan yang diambil (default: 25)
        min_similarity: Threshold minimum similarity (default: 0.5)
    
    Returns:
        Dictionary berisi ranking jurusan dengan skor ANP dan similarity
    """
    anp = ANPProcessor()
    
    # Load semua jurusan dari database
    all_majors = anp.load_majors_from_db()
    
    if not all_majors:
        raise ValueError("Tidak ada jurusan yang tersedia untuk dianalisis")
    
    # STEP 1: Hitung Cosine Similarity untuk SEMUA jurusan
    student_vector = np.array([riasec_scores.get(c, 0) for c in anp.riasec_types])
    norm_student = np.linalg.norm(student_vector)
    
    similarity_scores = {}
    for major, profile in all_majors.items():
        major_vector = np.array([profile[c] for c in anp.riasec_types])
        norm_major = np.linalg.norm(major_vector)
        
        if norm_student > 0 and norm_major > 0:
            similarity = float(np.dot(student_vector, major_vector) / (norm_student * norm_major))
        else:
            similarity = 0.0
        
        similarity_scores[major] = similarity
    
    # STEP 2: Filter jurusan
    # Urutkan berdasarkan similarity (descending)
    sorted_by_similarity = sorted(similarity_scores.items(), key=lambda x: x[1], reverse=True)
    
    # Filter: similarity >= threshold AND ambil top_n
    filtered_majors = [
        major for major, sim in sorted_by_similarity 
        if sim >= min_similarity
    ][:top_n]
    
    # Jika tidak ada yang lolos filter, ambil top_n saja (tanpa threshold)
    if not filtered_majors:
        filtered_majors = [major for major, _ in sorted_by_similarity[:top_n]]
    
    print(f"[PRE-FILTER] Pre-filter: {len(filtered_majors)} jurusan lolos dari {len(all_majors)} total")
    print(f"   Threshold: similarity >= {min_similarity}, max {top_n} jurusan")
    
    # STEP 3: Jalankan Pure ANP pada filtered majors
    anp_results = anp.calculate_anp_scores(riasec_scores, filtered_majors)
    
    # STEP 4: Tambahkan similarity score ke hasil
    for major, data in anp_results['ranked_majors']:
        data['similarity'] = similarity_scores.get(major, 0)
    
    # Update metadata
    anp_results['methodology'] = 'Pre-filtered ANP (Cosine Similarity + Pure ANP)'
    anp_results['prefilter_details'] = {
        'total_majors': len(all_majors),
        'filtered_count': len(filtered_majors),
        'top_n': top_n,
        'min_similarity': min_similarity,
        'similarity_scores': {
            major: similarity_scores[major] 
            for major in filtered_majors
        }
    }
    
    # Update top_5 dengan similarity
    for item in anp_results['top_5_majors']:
        major_name = item['major_name']
        item['similarity'] = similarity_scores.get(major_name, 0)
    
    return anp_results
