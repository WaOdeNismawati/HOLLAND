from utils.anp import ANPProcessor
import numpy as np

anp = ANPProcessor()

# Test pairwise matrix
scores = {
    "Realistic": 0.65,
    "Investigative": 1.00,
    "Artistic": 0.35,
    "Social": 0.50,
    "Enterprising": 0.45,
    "Conventional": 0.85
}

print("Testing Pairwise Matrix...")
matrix = anp.build_pairwise_matrix(scores)

print("\nPairwise Comparison Matrix:")
print("       ", "  ".join([t[:3] for t in anp.riasec_types]))
for i, t in enumerate(anp.riasec_types):
    row = "  ".join([f"{matrix[i,j]:.3f}" for j in range(6)])
    print(f"{t[:3]}: {row}")

# Calculate priorities
priorities, lambda_max = anp.calculate_priority(matrix)
print("\nPriority Vector:")
for i, t in enumerate(anp.riasec_types):
    print(f"  {t}: {priorities[i]:.6f}")

# Check consistency
ci, cr, is_consistent = anp.compute_consistency_ratio(lambda_max, 6)
print(f"\nConsistency Check:")
print(f"  Lambda Max: {lambda_max:.6f}")
print(f"  CI: {ci:.6f}")
print(f"  CR: {cr:.6f}")
print(f"  Consistent: {is_consistent}")

# Check sum of priorities
print(f"\nSum of priorities: {np.sum(priorities):.6f} (should be 1.0)")
