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

# Build supermatrix
pairwise_matrix = anp.build_pairwise_matrix(scores)
criteria_priorities, lambda_max = anp.calculate_priority(pairwise_matrix)
criteria_block = anp.normalize_columns(pairwise_matrix)

supermatrix, criteria_names, alternative_names = anp.build_supermatrix(
    scores, majors_data, criteria_block, criteria_priorities
)

print("Supermatrix Analysis:")
print(f"  Size: {supermatrix.shape[0]} x {supermatrix.shape[1]}")
print(f"  Column sums all = 1.0: {np.allclose(np.sum(supermatrix, axis=0), 1.0)}")

# Test convergence with different settings
print("\nConvergence Tests:")

test_configs = [
    (100, 1e-6),
    (200, 1e-6),
    (100, 1e-4),
    (500, 1e-6),
]

for max_iter, tol in test_configs:
    limit_matrix, iterations, converged = anp.limit_supermatrix(
        supermatrix, max_iterations=max_iter, tolerance=tol
    )
    print(f"  max_iter={max_iter}, tol={tol}: converged={converged} ({iterations} iterations)")
    
    if converged:
        # Extract priorities
        n_criteria = len(criteria_names)
        alt_block = limit_matrix[n_criteria:, :n_criteria]
        alt_priorities = alt_block.mean(axis=1)
        alt_priorities = alt_priorities / np.sum(alt_priorities)
        
        # Show top 5
        indices = np.argsort(alt_priorities)[::-1]
        print("    Top 5:")
        for i in range(5):
            idx = indices[i]
            major = alternative_names[idx]
            score = alt_priorities[idx]
            print(f"      {i+1}. {major}: {score:.6f}")
        break
