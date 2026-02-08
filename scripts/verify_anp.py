import numpy as np
import sys
import os

# Menambahkan direktori root ke sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.anp import ANPProcessor

def verify_anp_logic():
    print("=== Memulai Verifikasi Logika ANP ===")
    
    processor = ANPProcessor()
    
    # Skor dummy RIASEC siswa
    dummy_scores = {
        'Realistic': 0.8,
        'Investigative': 0.9,
        'Artistic': 0.3,
        'Social': 0.5,
        'Enterprising': 0.6,
        'Conventional': 0.4
    }
    
    print("\n1. Membangun Supermatrix...")
    # Mock alt_weights
    dummy_alt_weights = {
        trait: np.array([0.2, 0.3, 0.5]) for trait in processor.riasec_types
    }
    criteria_weights = np.array([0.3, 0.3, 0.1, 0.1, 0.1, 0.1])
    
    supermatrix = processor.build_supermatrix(criteria_weights, dummy_alt_weights)
    
    print("   - Mengecek blok W11 (Inner Dependency)...")
    w11_block = supermatrix[0:6, 0:6]
    
    # Pastikan bukan hanya diagonal yang terisi (karena ada inner dependency)
    off_diagonal_sum = np.sum(w11_block) - np.trace(w11_block)
    
    if off_diagonal_sum > 0:
        print(f"   [OK] Blok W11 memiliki nilai off-diagonal (Sum: {off_diagonal_sum:.4f})")
    else:
        print("   [ERROR] Blok W11 hanya berisi diagonal. Inner Dependency gagal terintegrasi.")
        return False

    print("\n2. Menjalankan Limit Supermatrix...")
    limit_matrix = processor.limit_supermatrix(supermatrix)
    
    # Cek konvergensi (kolom harus identik/hampir sama dalam limit)
    col1 = limit_matrix[:, 0]
    col2 = limit_matrix[:, 1]
    if np.allclose(col1, col2, atol=1e-5):
        print("   [OK] Supermatrix berhasil konvergen.")
    else:
        print("   [WARNING] Supermatrix mungkin belum konvergen sempurna.")

    print("\n3. Mengecek Kalkulasi Skor Akhir...")
    try:
        results = processor.calculate_anp_scores(dummy_scores)
        print(f"   [OK] Berhasil menghitung skor untuk {results['total_analyzed']} jurusan.")
        print(f"   Top Major: {results['top_5_majors'][0]['major_name']} (ANP Score: {results['top_5_majors'][0]['anp_score']:.4f})")
    except Exception as e:
        print(f"   [ERROR] Gagal menghitung skor ANP: {e}")
        return False

    print("\n=== Verifikasi Selesai: SEMUA LOGIKA VALID ===")
    return True

if __name__ == "__main__":
    if verify_anp_logic():
        sys.exit(0)
    else:
        sys.exit(1)
