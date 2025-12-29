from utils.anp import ANPProcessor
import numpy as np

anp = ANPProcessor()
majors_data = anp.load_majors_from_db()

scores = {
    "Realistic": 0.65,
    "Investigative": 1.00,
    "Artistic": 0.35,
    "Social": 0.50,
    "Enterprising": 0.45,
    "Conventional": 0.85
}

print(f"Total majors: {len(majors_data)}")

# Build pairwise and get priorities
pairwise_matrix = anp.build_pairwise_matrix(scores)
criteria_priorities, lambda_max = anp.calculate_priority(pairwise_matrix)
criteria_block = anp.normalize_columns(pairwise_matrix)

print("\nCriteria Priorities:")
for i, t in enumerate(anp.riasec_types):
    print(f"  {t}: {criteria_priorities[i]:.6f}")

# Build supermatrix
supermatrix, criteria_names, alternative_names = anp.build_supermatrix(
    scores, majors_data, criteria_block, criteria_priorities
)

print(f"\nSupermatrix size: {supermatrix.shape}")
print(f"Criteria: {len(criteria_names)}")
print(f"Alternatives: {len(alternative_names)}")

# Check supermatrix properties
print("\nSupermatrix column sums (should all be 1.0):")
col_sums = np.sum(supermatrix, axis=0)
print(f"  Min: {np.min(col_sums):.6f}")
print(f"  Max: {np.max(col_sums):.6f}")
print(f"  Mean: {np.mean(col_sums):.6f}")
print(f"  All ≈ 1.0: {np.allclose(col_sums, 1.0, atol=1e-6)}")

# Try limit supermatrix with more info
print("\nTesting convergence...")
limit_matrix, iterations, converged = anp.limit_supermatrix(supermatrix, max_iterations=100, tolerance=1e-6)

print(f"  Iterations: {iterations}")
print(f"  Converged: {converged}")

if not converged:
    print("\n  WARNING: Did not converge! Testing with:")
    # Test with looser tolerance
    limit_matrix2, it2, conv2 = anp.limit_supermatrix(supermatrix, max_iterations=200, tolerance=1e-4)
    print(f"    200 iter, tol=1e-4: {conv2} ({it2} iterations)")
    
    # Check if alternating
    test_matrix = supermatrix.copy()
    for i in range(5):
        test_matrix = np.dot(test_matrix, supermatrix)
        for j in range(test_matrix.shape[1]):
            col_sum = np.sum(test_matrix[:, j])
            if col_sum > 0:
                test_matrix[:, j] /= col_sum
    
    diff = np.max(np.abs(test_matrix - limit_matrix[:5,:]))
    print(f"    Difference after 5 iterations: {diff:.10f}")
