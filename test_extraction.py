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

# Get limit matrix with more iterations
limit_matrix, iterations, converged = anp.limit_supermatrix(
    supermatrix, max_iterations=500, tolerance=1e-6
)

print(f"Converged: {converged} ({iterations} iterations)\n")

n_criteria = len(criteria_names)
alt_block = limit_matrix[n_criteria:, :n_criteria]

print("Alternative block shape:", alt_block.shape)
print("(Should be: 45 alternatives x 6 criteria)\n")

# Check if columns are similar (should be in converged limit matrix)
print("Column similarity check:")
for i in range(n_criteria):
    col_i = alt_block[:, i]
    for j in range(i+1, n_criteria):
        col_j = alt_block[:, j]
        diff = np.max(np.abs(col_i - col_j))
        print(f"  Max diff col {i} vs col {j}: {diff:.10f}")

print("\nExtraction methods comparison:")
print("="*60)

# Method 1: Mean across criteria (current)
priorities_mean = alt_block.mean(axis=1)
priorities_mean = priorities_mean / np.sum(priorities_mean)

# Method 2: First column only
priorities_col0 = alt_block[:, 0]
priorities_col0 = priorities_col0 / np.sum(priorities_col0)

# Method 3: Weighted by criteria priorities
weighted = np.dot(alt_block, criteria_priorities)
priorities_weighted = weighted / np.sum(weighted)

print("\nMethod 1: Mean across columns")
indices = np.argsort(priorities_mean)[::-1]
for i in range(5):
    idx = indices[i]
    print(f"  {i+1}. {alternative_names[idx]:<30} {priorities_mean[idx]:.6f}")

print("\nMethod 2: First column only")
indices = np.argsort(priorities_col0)[::-1]
for i in range(5):
    idx = indices[i]
    print(f"  {i+1}. {alternative_names[idx]:<30} {priorities_col0[idx]:.6f}")

print("\nMethod 3: Weighted by criteria priorities")
indices = np.argsort(priorities_weighted)[::-1]
for i in range(5):
    idx = indices[i]
    print(f"  {i+1}. {alternative_names[idx]:<30} {priorities_weighted[idx]:.6f}")

# Check which majors have high I and C
print("\nMajors with high I & C (expected matches):")
for major, profile in sorted(majors_data.items(), key=lambda x: x[1]["Investigative"] + x[1]["Conventional"], reverse=True)[:5]:
    print(f"  {major:<30} I={profile['Investigative']:.2f} C={profile['Conventional']:.2f}")
